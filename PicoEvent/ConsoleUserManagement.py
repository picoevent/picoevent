from PicoEvent.Database import Database, DatabaseException
from PicoEvent.AnalystUser import AnalystUser


class ConsoleUserManager:
    def __init__(self):
        self._db = Database()
        self._session_token = None
        self._user_id = None

    @staticmethod
    def main_menu():
        print("""Administrator Main Menu

        1.) List Users
        2.) Create User
        3.) List Permissions for User
        4.) Assign User Permission
        5.) Revoke User Permission
        6.) Reset password
        """)

    def reset_password(self, email, new_passwd):
        try:
            result = self._db.reset_password(email, new_passwd)
            if result:
                print("Password successfully changed.")
        except DatabaseException:
            print("Database Exception: Could not change password.")

    def login_admin(self, passwd):
        result = self._db.login("admin", passwd)
        if result:
            self._session_token = result[0]
            self._user_id = result[1]
            return True
        return False

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

    def create_user(self, email, passwd, name):
        try:
            result = self._db.create_user(email, passwd, name, "console")
            print("Created new user with ID: {0}".format(result[0]))
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
                    event_id = self._db.log_event({"assigned_by": "Administator",
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


if __name__ == "__main__":
    mgr = ConsoleUserManager()
    print("PicoEvent Console User Administration Interface")
    logged_in = False
    while not logged_in:
        password = input("Administrator password: ")
        logged_in = mgr.login_admin(password)
    mgr.main_menu()
    while 1:
        user_input = input("> ")
        choice = int(user_input)
        if choice > 0 < 7:
            if choice == 1:
                mgr.list_users()
            elif choice == 2:
                email_address = input("E-mail address/login: ")
                password = input("Password: ")
                full_name = input("Full Name: ")
                mgr.create_user(email_address, password, full_name)
            elif choice == 3:
                user_id = input("User id: ")
                mgr.list_permissions_for_user_id(user_id)
            elif choice == 4:
                available_permissions = []
                for each in AnalystUser.ALL_PERMISSIONS:
                    available_permissions.append(each)
                user_id = input("User id: ")
                for x in range(1, len(available_permissions) + 1):
                    print("{0}) {1}".format(x, available_permissions[x - 1]))
            elif choice == 5:
                print("Not yet implemented.")
            elif choice == 6:
                print("Change user's password.")
                email_address = input("E-mail address/login: ")
                new_password = input("New password: ")
