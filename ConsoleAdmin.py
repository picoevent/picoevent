#  This is like manage.py

from PicoEvent.Database import Database, DatabaseException
from PicoEvent.Environment import Environment
import sys
import logging
import json
import binascii
import os
from datetime import timedelta

VERSION = 0.1
MAX_LOGIN_ATTEMPTS = 5


class ConsoleMenu:
    def main_menu(self):
        pass

    @staticmethod
    def select_item(min_value: int, max_value: int) -> int:
        if max_value <= min_value:
            raise ValueError
        while True:
            raw_input = input("> ")
            x = int(raw_input)
            if min_value <= x <= max_value:
                return x
            print("Accepted inputs are integers between {0} and {1}".format(min, max))

    @staticmethod
    def confirm() -> bool:
        raw_input = input("(Y\n) ")
        while True:
            if raw_input == "Y":
                return True
            if raw_input == "n":
                return False
            print("The only excepted inputs are 'Y' and 'N'")


class ConsoleUserManager(ConsoleMenu):
    MAIN_MENU_CHOICES = ["List Users",
                         "Create User",
                         "List Permissions for User",
                         "Assign User Permission",
                         "Revoke User Permission",
                         "List Event Types",
                         "Reset Password",
                         "Back to Main Menu"]

    def __init__(self, environment, user_id, session_token, use_logger=None):
        self._db = Database(env=environment, logger=use_logger)
        self._session_token = session_token
        self._user_id = user_id

    def main_menu(self):
        print("User Administration Menu\n")
        x = 1
        choices = ConsoleUserManager.MAIN_MENU_CHOICES
        for each in choices:
            print("{0}.) ".format(x) + each)
            x += 1

        choice = self.select_item(1, len(choices) + 1)

        if choice == 1:
            self.list_users()
        elif choice == 2:
            self.create_user()
        elif choice == 3:
            query_user_id = int(input("List permissions for user_id: "))
            self.list_permissions_for_user_id(query_user_id)
        elif choice == 4:
            query_user_id = int(input("Assign view-event-id permission for user_id: "))
            query_event_type_id = int(input("Event type id: "))
            self.assign_permission_for_user_id(query_user_id, "view", query_event_type_id)
        elif choice == 5:
            print("Not yet implemented.")
        elif choice == 6:
            event_types = db.list_event_types()
            print("ID\tEvent Type")
            for each_event in event_types:
                print("{0}\t{1}".format(each_event[0], each_event[1]))
        elif choice == 7:
            username = input("Reset password for user with email/username: ")
            new_password = input("New password: ")
            self.reset_password(username, new_password)
        elif choice == 8:
            return
        input("\nPress Enter to continue")
        self.main_menu()

    def reset_password(self, email, new_passwd):
        try:
            self._db.reset_password(email, new_passwd)
            print("Password successfully changed.")
        except DatabaseException:
            print("Database Exception: Could not change password.")

    def list_users(self):
        try:
            user_list = self._db.list_analyst_user_info()
            # user_id, email_address, full_name, last_logged_in
            print("User ID\tLogin/E-mail\tFull Name\tLast Logged In\n\n")
            for each_user in user_list:
                print("{0}\t{1}\t{2}\t{3}".format(each_user[0],
                                                  each_user[1],
                                                  each_user[2],
                                                  each_user[3]))
            print("\n\n")
        except DatabaseException:
            print("Database error.")

    def create_user(self, email=None, passwd=None, name=None):
        if email is None:
            email = input("E-mail address: ")
        if passwd is None:
            passwd = input("Password: ")
        if name is None:
            name = input("Name: ")

        try:
            new_user = self._db.create_user(email, passwd, name, "console")
            print("Created new user with ID: {0}".format(new_user[0]))
        except DatabaseException:
            print("Could not create a new user.")

    def list_permissions_for_user_id(self, uid):
        try:
            user_permissions = self._db.list_permissions_for_user_id(uid)
            print("ACL ID\tPermission\tEvent Type ID\tCreated\tRevoked\n")
            for each_permission in user_permissions:
                print("{0}\t{1}\t{2}\t{3}\t{4}".format(each_permission[0],
                                                       each_permission[2],
                                                       each_permission[1],
                                                       each_permission[6],
                                                       "NO"))
        except DatabaseException:
            print("Could not create a new user.")

    def assign_permission_for_user_id(self, uid, permission, event_type_id=None):
        if permission is "view-event-type" and event_type_id:
            event_type = None
            all_event_types = self._db.list_event_types()
            for each_event_type in all_event_types:
                if each_event_type[0] == event_type_id:
                    event_type = each_event_type[1]
                    break
            if event_type:
                logged_event_type_id = None
                for each_event_type in all_event_types:
                    if each_event_type[1] is "Add Permission":
                        logged_event_type_id = each_event_type[0]
                        break
                try:
                    event_id = self._db.log_event({"assigned_by": "Administrator",
                                                   "ip_addr": "console",
                                                   "event_type": event_type,
                                                   "event_type_id": event_type_id},
                                                  logged_event_type_id,
                                                  0,
                                                  uid)
                    new_acl_id = self._db.assign_permission_for_user_id(uid,
                                                                        permission,
                                                                        event_id,
                                                                        event_type_id)
                    print("Assigned new permission ID {0} to user_id {1}.".format(new_acl_id,
                                                                                  uid))
                except DatabaseException:
                    print("Could not assign a new permission.")

    def revoke_permission_for_user_id(self, uid, permission_id):
        pass


class ConsoleMainMenuManager(ConsoleMenu):
    STATES = ["DATABASE_NOT_SETUP", "USER_ADMIN"]
    MAIN_MENU = ["Reset admin password", "List API Keys", "Generate new API key", "Reset Quota",
                 "User administration", "Exit"]

    def __init__(self, console_env, use_logger=None):
        self._config = config
        self._logger = use_logger
        self._state = "DATABASE_NOT_SETUP"
        self._user_admin_mgr = None
        self._env = console_env
        self._user_id = -1
        self._session_token = None

    def user_admin_mode(self, user_id, session_token):
        self._user_admin_mgr = ConsoleUserManager(self._env, user_id, session_token,
                                                  use_logger=self._logger)
        self._user_id = user_id
        self._session_token = session_token

        self._state = "USER_ADMIN"

    def change_administrator_password(self):
        _db = Database(self._logger, False, False, self._env)
        admin_uid = _db.admin_user_id
        if admin_uid > 0:
            new_password = input("New administrator password: ")
            try:
                _db.reset_password("admin", new_password)
            except DatabaseException:
                print("Database exception: unable to reset administrators password.")
        else:
            print("Invalid administrator user ID, database could be corrupted.")
            print("Consider creating a new empty database and starting over.\n")

    def display_menu(self):
        if self._state == "USER_ADMIN":
            self._user_admin_mgr.main_menu()

        print("Console Administration Main Menu\n")
        try:
            test_db = Database(self._logger, True, False, self._env)
            del test_db
        except DatabaseException:
            print("Warning: Test database does not exist or is not accessible with supplied credentials.")
        print("\n")
        x = 1
        for choice in ConsoleMainMenuManager.MAIN_MENU:
            print("{0}.) {1}".format(x, choice))
            x += 1
        choice = self.select_item(1, 3)
        if choice == 1:
            self.change_administrator_password()
        elif choice == 2:
            _db = Database(self._logger, False, False, self._env)
            # node_id, api_key, created, quota, next_reset, events_posted
            all_api_keys = _db.list_api_keys()
            del _db
            print("Node ID\tAPI Key\tCreated\tQuota\tNext Reset\tEvents Posted")
            for each_key in all_api_keys:
                print("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(each_key[0], each_key[1], each_key[2].isoformat(),
                                                                 each_key[3], each_key[4], each_key[5]))
        elif choice == 3:
            print("Would you like to set a custom quota reset interval for the new API key?")
            custom_reset_seconds = None
            if self.confirm():
                day_seconds = 3600 * 24
                print("Choose a quota reset interval in seconds between 1 and {0}".format(day_seconds))
                custom_reset_seconds = self.select_item(1, day_seconds)
            print("Would you like to set a custom quota for the new API key?")
            custom_quota = None
            if self.confirm():
                print("Choose a custom quota between 100 and 50000")
                custom_quota = self.select_item(100, 50000)
            new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
            _db = Database(self._logger, False, False, self._env)
            node_id = _db.create_api_key(new_api_key, custom_quota, custom_reset_seconds)
            if node_id > 0:
                api_key_info = _db.validate_api_key(new_api_key)
                print("New API Key {0} generated with a quota of {1}, next reset {1}.".format(api_key_info[1],
                                                                                              api_key_info[4],
                                                                                              api_key_info[5]))
            else:
                print("Could not create a new API key, check log file for more info.")
            del _db
        elif choice == 4:
            print("Reset quota (you will need the node id from the API key list)")
            _db = Database(self._logger, False, False, self._env)
            all_node_ids = set()
            for each_api_key in _db.list_api_keys:
                all_node_ids.add(each_api_key[0])
            repeat = True
            node_id = None
            while repeat:
                user_input = int(input("Node ID: "))
                if user_input in all_node_ids:
                    node_id = user_input
                    break
                print("Node ID {0} not in the list of active API keys. Try again?")
                repeat = self.confirm()
            if node_id:
                next_reset = _db.reset_quota
                print("Would you like to set a custom reset interval (default: 3600 seconds)")
                if self.confirm():
                    day_seconds = 3600 * 24
                    print("Choose a quota reset interval in seconds between 1 and {0}".format(day_seconds))
                    next_reset = datetime.now() + timedelta(seconds=self.select_item(1, day_seconds))
                _db.reset_quota(node_id, next_reset)
        elif choice == 5:
            self.user_admin_mode(self._user_id, self._session_token)
        else:
            print("Bye")
            sys.exit(0)
        input("Press Enter to continue")


def setup_file_logging(log_path):
    file_logger = logging.getLogger("picoevent console")
    file_logger.setLevel(logging.INFO)
    # create file handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add the handler to the logger
    file_logger.addHandler(fh)

    file_logger.info("picoevent console: startup")
    return file_logger


if __name__ == "__main__":
    print("picoevent {0}\nConsole Configuration Utility".format(VERSION))
    config = None
    try:
        config_stream = open("PicoEvent/config/config.json", "r")
        config = json.load(config_stream)
        config_stream.close()
    except IOError:
        print("Could not open the PicoEvent/config/config.json file for reading. Exiting.")
        sys.exit()

    logger = None
    if "console_logging_enabled" in config and config["console_logging_enabled"]:
        if "console_log_file" in config:
            print("Logging to file: {0}".format(config["console_log_file"]))
            logger = setup_file_logging(config["console_log_file"])

    env = Environment(config["mysql_host"], "", config["mysql_user"], config["mysql_passwd"], config["mysql_db"],
                      config["mysql_test_db"], 0, 3600, "", "")

    context_manager = ConsoleMainMenuManager(env, logger)
    db = Database(env=env, logger=logger)
    session_id = None
    admin_user_id = -1

    def login_admin():
        attempts = 0
        while attempts < MAX_LOGIN_ATTEMPTS:
            password = input("admin password: ")
            try:
                login_info = db.login("admin", password)
                return login_info[0]
            except DatabaseException:
                attempts += 1
                print("Login failed, try again. ({0} attempts remaining)".format(MAX_LOGIN_ATTEMPTS - attempts))
        print("Maximum attempts exceeded. Exiting...")

    if db:
        message = "Successfully connected to database: {0}".format(config["mysql_db"])
        print(message)
        logger.info(message)

        admin_user_id = db.admin_user_id

        if admin_user_id > 0:
            message = "Administrator user_id is {0}, login now?".format(admin_user_id)
            print(message)
            user_input = input("(Y/n)")
            if user_input == "Y":
                context_manager.user_admin_mode(admin_user_id, login_admin())
                context_manager.display_menu()
            else:
                sys.exit(0)
        else:
            message = "admin user not found, database might be corrupted of empty."
            print(message)
            logger.info(message)
            user_input = input("Clear and install schema (Y/n) ")
            if user_input == "Y":
                result = db.mysql_setup()
                if result > 0:
                    print("Could not install schema, check log for details.")
                    sys.exit(1)
                result = db.mysql_admin_setup()
                if result > 0:
                    print("Could not create Administrator user, check log for details.")
                    sys.exit(1)
            else:
                sys.exit(0)
