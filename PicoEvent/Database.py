from PicoEvent.AnalystUser import AnalystUser
from PicoEvent.Environment import EnvironmentBase
from MySQLdb import connect, ProgrammingError, Error
from hashlib import sha256
from datetime import datetime, timedelta
import binascii
import json
import os
import re
import time
import sys

CONFIG_DIR = "PicoEvent/config/"

COUNT_REGEX = re.compile("^SELECT COUNT")

DEFAULT_EVENTS = {"Create API Key",
                  "Change Quota",
                  "Manual Reset",
                  "Suspend API Key",
                  "Add Permission",
                  "Create Analyst User",
                  "Remove Permission",
                  "Add Event Type",
                  "Reset Password"}


class DatabaseException(Exception):
    """ Database module exception """
    pass


class DatabaseNoSchema(DatabaseException):
    """ Database no schema exception """
    pass


class DatabaseNoAdmin(DatabaseException):
    """ Administrator user not configured """
    pass


class DatabaseReadOnlyException(DatabaseException):
    """ Function cannot be used in read_only mode """
    pass


class DatabaseNotFoundException(DatabaseException):
    """ Record not found """
    pass


class Database:
    def __init__(self, logger=None, test: bool = False, read_only: bool = False, env: EnvironmentBase = None):
        self._logger = logger
        if env:
            self._env = env
            self._config = env.db_config
            self._quota_reset_interval = timedelta(seconds=env.db_config["rate_limit_reset"])
            self._rate_limit_quota = env.db_config["rate_limit_quota"]
        else:
            try:
                config_stream = open("config/" + "config.json", "r")
                self._config = json.load(config_stream)
                config_stream.close()
            except IOError:
                if self._logger:
                    self._logger.error("IOError opening config file.")
                else:
                    print("IOError opening config file.")
            self._quota_reset_interval = timedelta(hours=1)
            self._rate_limit_quota = 1000
            self._env = None

        self._read_only = read_only

        if test:
            db_name = self._config["mysql_test_db"]
        else:
            db_name = self._config["mysql_db"]
        self._db = connect(self._config["mysql_host"],
                           self._config["mysql_user"],
                           self._config["mysql_passwd"],
                           db_name)

        if test:
            # clear the test database for unit testing
            c = self._db.cursor()
            sql_stream = open("config/picoevent-mysql.sql", "r")
            sql_data = sql_stream.read()
            sql_stream.close()

            c.execute(sql_data)
            hash_data = ("admin" + "test_password").encode("utf-8")
            password_hash = sha256(hash_data).hexdigest()
            sql = "INSERT INTO users (email_address,password,full_name) VALUES ('admin',%s,'Administrator');"
            try:
                c.execute(sql, (password_hash,))
                self._db.commit()
            except Error as e:
                try:
                    error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    error_message = "MySQL Error: %s" % (str(e),)
                print("MySQL Error: " + error_message)
        else:
            # Do not perform sanity check when doing unit tests
            c = self._db.cursor()
            try:
                c.execute("SELECT email_address FROM users WHERE email_address='admin';")
                row = c.fetchone()
                if row:
                    if row[0] != "admin":
                        self.mysql_admin_setup()
                else:
                    self.mysql_admin_setup()
            except ProgrammingError:
                self.mysql_setup()
                time.sleep(5)
                self.mysql_admin_setup()

    @property
    def rate_limit_quota(self) -> int:
        return self._rate_limit_quota

    @property
    def next_quota_reset(self) -> datetime:
        return datetime.now() + self._quota_reset_interval

    def get_event_data(self, event_id: int) -> tuple:
        sql = "SELECT event_id, event_log.event_type_id, node_id, user_id, event_data, created, event_type.event_type "
        sql += "FROM event_log INNER JOIN event_type ON event_type.event_type_id=event_log.event_type_id"
        sql += " WHERE event_id=%s;"
        c = self._db.cursor()
        try:
            c.execute(sql, (event_id,))
            row = c.fetchone()
            if row:
                return row
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseNotFoundException

    def retrieve_events(self, user_id: int = None, event_type_id: int = None, node_id=None, since: datetime = None,
                        until: datetime = None, limit=100) -> list:
        sql = "SELECT event_id, event_type_id, node_id, user_id, created FROM event_log"
        return self._concat_sql(sql, user_id, event_type_id, node_id, since, until, limit)

    def get_event_count(self, user_id: int = None, event_type_id: int = None, node_id=None, since: datetime = None,
                        until: datetime = None) -> int:
        sql = "SELECT COUNT(*) FROM event_log"
        return self._concat_sql(sql, user_id, event_type_id, node_id, since, until)

    def _concat_sql(self, sql, user_id: int = None, event_type_id: int = None, node_id=None, since: datetime = None,
                    until: datetime = None, limit: int = None):
        args = []
        if user_id or event_type_id or node_id:
            sql += " WHERE "
            if user_id:
                args.append(user_id)
                sql += "user_id=%s"
                if event_type_id:
                    args.append(event_type_id)
                    if len(args) > 1:
                        sql += " AND "
                    sql += "event_type_id=%s"
                    if node_id:
                        args.append(node_id)
                        if len(args) > 1:
                            sql += " AND "
                        sql += "node_id=%s"
            elif event_type_id:
                args.append(event_type_id)
                if len(args) > 1:
                    sql += " AND "
                sql += "event_type_id=%s"
                if node_id:
                    args.append(node_id)
                    if len(args) > 1:
                        sql += " AND "
                    sql += "node_id=%s"
            elif node_id:
                args.append(node_id)
                sql += "node_id=%s"

        try:
            return self._events_between(sql, args, since, until, limit)
        except DatabaseException:
            raise DatabaseException

    def _events_between(self, sql, args: list, since: datetime = None, until: datetime = None, limit: int = None):
        def append_ordering(sql_stmt, args):
            if not COUNT_REGEX.search(sql_stmt):
                if limit:
                    args.append(int(limit))
                    return sql_stmt + " ORDER BY event_id DESC LIMIT %s"
                else:
                    return sql_stmt + " ORDER BY event_id DESC"
            else:
                return sql_stmt

        c = self._db.cursor()
        try:
            if since and until:
                sql += " AND created>%s AND created<%s"
                args.append([since, until])
                sql = append_ordering(sql, args)
                self._logger.debug(sql)
                c.execute(sql, tuple(args))
            elif since:
                sql += " AND created>%s"
                args.append(since)
                sql = append_ordering(sql, args)
                self._logger.debug(sql)
                c.execute(sql, tuple(args))
            elif until:
                sql += " AND created<%s"
                args.append(until)
                sql = append_ordering(sql, args)
                self._logger.debug(sql)
                c.execute(sql, tuple(args))
            else:
                sql = append_ordering(sql, args)
                self._logger.debug(sql)
                c.execute(sql, tuple(args))

            if c.rowcount > 1:
                output = []
                for row in c:
                    output.append(row)
                return output  # returns a list of event tuples
            else:
                row = c.fetchone()
                if len(row) > 1:
                    return row  # returns a single event tuple
                else:
                    return row[0]  # returns a count
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def validate_api_key(self, api_key) -> tuple:
        sql = "SELECT node_id, created, quota, next_reset, events_posted, suspension_event_id FROM api_keys"
        sql += " WHERE api_key=%s"
        c = self._db.cursor()
        try:
            c.execute(sql, (api_key,))
            row = c.fetchone()
            if row:
                return row
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def update_quota(self, node_id):
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "UPDATE api_keys SET events_posted = events_posted+1 WHERE node_id=%s"
        c = self._db.cursor()
        try:
            c.execute(sql, (node_id,))
            self._db.commit()
            return True
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return False

    def reset_quota(self, node_id, next_reset) -> bool:
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "UPDATE api_keys SET events_posted=%s AND next_reset=%s WHERE node_id=%s"

        c = self._db.cursor()
        try:
            c.execute(sql, (0, next_reset, node_id))
            self._db.commit()
            return True
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return False

    def log_event(self, event_data: dict, event_type_id: int, node_id: int, user_id: int = None) -> int:
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "INSERT INTO event_log (node_id, user_id, event_data, event_type_id) VALUES (%s, %s, %s, %s)"
        c = self._db.cursor()
        try:
            c.execute(sql, (node_id,
                            user_id,
                            json.dumps(event_data),
                            event_type_id))
            self._db.commit()
            return c.lastrowid
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)

        raise DatabaseException

    def create_event_type(self, new_event_type) -> int:
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "INSERT INTO event_type (event_type) VALUE (%s)"
        c = self._db.cursor()
        try:
            c.execute(sql, (new_event_type,))
            self._db.commit()
            last_row_id = c.lastrowid
            if last_row_id:
                return last_row_id
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return -1

    def list_event_types(self) -> list:
        sql = "SELECT event_type_id, event_type FROM event_type;"
        c = self._db.cursor()
        output = []
        try:
            c.execute(sql)
            for row in c:
                output.append((row[0], row[1]))
            return output
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def create_api_key(self, api_key: str, rate_limit_quota: int = None, next_reset_seconds: int = None) -> int:
        if self._read_only:
            raise DatabaseReadOnlyException

        if rate_limit_quota:
            quota = rate_limit_quota
        else:
            quota = self._rate_limit_quota

        if next_reset_seconds:
            reset_interval = datetime.now() + timedelta(seconds=next_reset_seconds)
        else:
            reset_interval = self.next_quota_reset

        if re.compile("[A-F0-9]{16}").match(api_key):
            sql = "INSERT INTO api_keys (api_key,quota,next_reset) VALUE (%s,%s,%s)"
            c = self._db.cursor()
            try:
                c.execute(sql, (api_key,
                                quota,
                                reset_interval))
                self._db.commit()
                if c.rowcount == 1:
                    return c.lastrowid
            except Error as e:
                try:
                    error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    error_message = "MySQL Error: %s" % (str(e),)

                if self._logger:
                    self._logger.error(error_message)
                else:
                    print(error_message)
        return -1

    def suspend_api_key(self, node_id, event_id):
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "UPDATE api_keys SET suspension_event_id=%s WHERE node_id=%s"
        c = self._db.cursor()
        try:
            c.execute(sql, (node_id, event_id,))
            self._db.commit()
            return True
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return False

    def assign_permission_for_user_id(self, user_id: int, permission: str, assignment_event_id: int,
                                      event_type_id: int = None) -> int:
        if event_type_id:
            sql = """"INSERT INTO access_control_list (event_type_id,permission,assigned_event_id,user_id) VALUES 
            (%s,%s,%s,%s);"""
            args = (event_type_id, permission, assignment_event_id, user_id)
        else:
            sql = "INSERT INTO access_control_list (permission,assigned_event_id,user_id) VALUES (%s,%s,%s)"
            args = (permission, assignment_event_id, user_id)
        c = self._db.cursor()
        try:
            c.execute(sql, args)
            self._db.commit()
            return c.lastrowid
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def list_permissions_for_user_id(self, user_id):
        sql = "SELECT id, event_type_id, permission, assigned_event_id, revoked_event_id, created "
        sql += "FROM access_control_list WHERE user_id=%s"
        c = self._db.cursor()
        try:
            c.execute(sql, (user_id,))
            output = []
            for row in c:
                output.append(row)
            return output
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def reset_password(self, email_address, new_password):
        sql = "UPDATE users SET password=%s WHERE email_address=%s"
        password_hash = sha256((email_address + new_password).encode("utf-8")).hexdigest()
        c = self._db.cursor()
        try:
            c.execute(sql, (password_hash, email_address,))
            self._db.commit()
            return True
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def list_analyst_user_info(self, limit: int = None, offset: int = None) -> list:
        sql = "SELECT user_id, email_address, full_name, last_logged_in FROM users"
        args = []
        if limit:
            sql += " LIMIT=%s"
            args.append(limit)
        if offset:
            sql += " OFFSET=%s"
            args.append(offset)
        c = self._db.cursor()
        try:
            if len(args) > 0:
                c.execute(sql, tuple(args))
            else:
                c.execute(sql)
            output = []
            for row in c:
                output.append(row)
            return output
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def list_api_keys(self):
        sql = "SELECT node_id, api_key, created, quota, next_reset, events_posted, suspension_event_id FROM api_keys"
        c = self._db.cursor()
        try:
            c.execute(sql)
            output = []
            for row in c:
                output.append(row)
            return output
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def validate_session(self, session_token: str):
        sql = "SELECT user_id, email_address, full_name FROM users WHERE session_token=%s"
        c = self._db.cursor()
        try:
            c.execute(sql, (session_token,))
            row = c.fetchone()
            if row:
                if row[1] == "admin":
                    return AnalystUser(row[0], row[1], session_token, row[2], AnalystUser.ALL_PERMISSIONS, set())
                else:
                    user_permissions = self.list_permissions_for_user_id(row[0])
                    permissions = set()
                    available_event_ids = set()
                    # id, event_type_id, permission, assigned_event_id, revoked_event_id, created
                    for each_permission in user_permissions:
                        if each_permission[4] is None:
                            if each_permission[1] is None:
                                permissions.add(each_permission[2])
                            else:
                                available_event_ids.add(each_permission[1])
                    return AnalystUser(row[0], row[1], session_token, row[2], permissions, available_event_ids)
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def create_user(self, email_address: str, password: str, full_name: str, created_ip: str):
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "INSERT INTO users (email_address,password,created_ip,session_token,full_name) VALUES (%s,%s,%s,%s,%s)"
        password_hash = sha256((email_address + password).encode("utf-8")).hexdigest()
        new_session_token = binascii.hexlify(os.urandom(8))
        c = self._db.cursor()
        try:
            c.execute(sql, (email_address, password_hash, created_ip, new_session_token, full_name))
            self._db.commit()
            last_row_id = c.lastrowid
            return last_row_id, new_session_token
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return -1, None

    def login(self, email_address: str, password: str) -> tuple:
        if self._read_only:
            raise DatabaseReadOnlyException

        sql = "SELECT user_id, password FROM users WHERE email_address=%s;"
        c = self._db.cursor()
        try:
            c.execute(sql, (email_address,))
            row = c.fetchone()
            if row:
                password_hash = sha256((email_address + password).encode("utf-8")).hexdigest()
                if row[1] == password_hash:
                    new_session_token = binascii.hexlify(os.urandom(8))
                    sql = "UPDATE users SET session_token=%s WHERE user_id=%s"
                    c.execute(sql, (new_session_token, row[0]))
                    self._db.commit()
                    if c.rowcount == 1:
                        return new_session_token, row[0]
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        raise DatabaseException

    def mysql_admin_setup(self):
        admin_password = input("Choose a password for 'admin' account: ")
        hash_data = ("admin" + admin_password).encode("utf-8")
        pw_hash = sha256(hash_data)
        password_hash = pw_hash.hexdigest()

        c = self._db.cursor()
        sql = "INSERT INTO users (email_address,password,full_name) VALUES ('admin',%s,'Administrator');"
        try:
            c.execute(sql, (password_hash,))
            sql = "INSERT INTO event_type (event_type) VALUE (%s)"
            for each in DEFAULT_EVENTS:
                c.execute(sql, (each,))
            self._db.commit()
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
            return 1
        return 0

    def mysql_setup(self):
        c = self._db.cursor()

        print("Database not setup, install schema?")
        while True:
            console_input = input("(Y/n) ")
            if console_input == "Y":
                break
            elif console_input == "n":
                sys.exit()
            print("Acceptable values are Y or n")

        sql_stream = open(CONFIG_DIR + "picoevent-mysql.sql", "r")
        sql_data = sql_stream.read()
        sql_stream.close()
        try:
            c.execute(sql_data)
            self._db.commit()
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
            return 1
        return 0

    @property
    def admin_user_id(self) -> int:
        c = self._db.cursor()
        try:
            c.execute("SELECT user_id FROM users WHERE email_address=\"admin\"")
            row = c.fetchone()
            if row:
                return row[0]
        except Error as e:
            try:
                error_message = "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                error_message = "MySQL Error: %s" % (str(e),)

            if self._logger:
                self._logger.error(error_message)
            else:
                print(error_message)
        return -1
