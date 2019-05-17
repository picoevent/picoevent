#  This is like manage.py

from PicoEvent.Database import Database, DatabaseException
from PicoEvent.Environment import Environment
import sys
import logging
import json

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
                         "Exit"]

    def __init__(self, environment, user_id, session_token, use_logger=None):
        self._db = Database(logger=use_logger, env=environment)
        self._session_token = session_token
        self._user_id = user_id

    def main_menu(self):
        print("User Administration Menu\n")
        x = 1
        choices = ConsoleUserManager.MAIN_MENU_CHOICES
        for each in choices:
            print("{0}.) " + each)
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
            print("Bye")
            sys.exit(0)
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


class ConsoleMainMenuManager:
    STATES = ["DATABASE_NOT_SETUP", "USER_ADMIN"]

    def __init__(self, console_env, use_logger=None):
        self._config = config
        self._logger = use_logger
        self._state = "DATABASE_NOT_SETUP"
        self._user_admin_mgr = None
        self._env = console_env

    def user_admin_mode(self, user_id, session_token):
        self._user_admin_mgr = ConsoleUserManager(self._env, user_id, session_token)
        self._state = "USER_ADMIN"

    def display_menu(self):
        pass


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

    env = Environment(config["mysql_host"], "", config["mysql_user"], config["mysql_password"], config["mysql_db"],
                      config["mysql_test_db"], 0, 3600, "", "")

    db = Database(logger)
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
                session_id = login_admin()
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
                    print("Could not install schama, check log for details.")
                    sys.exit(1)
                result = db.mysql_admin_setup()
                if result > 0:
                    print("Could not create Administrator user, check log for details.")
                    sys.exit(1)
            else:
                sys.exit(0)
