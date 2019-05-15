import json


class AnalystUser:
    user_id: int
    email_address: str
    session_token: str
    full_name: str

    ALL_PERMISSIONS = {"add-event-type",
                       "create-api-key",
                       "view-all-event-types",
                       "change-quota",
                       "suspend-api-key",
                       "create-analyst",
                       "change-permissions",
                       "reset-password",
                       "manual-quota-reset",
                       "view-event-type"}

    def __init__(self,
                 user_id,
                 email_address,
                 session_token,
                 full_name,
                 permissions: set,
                 view_event_type_ids: set):
        self.user_id = user_id
        self.email_address = email_address
        self.session_token = session_token
        self.full_name = full_name
        self._permissions = permissions
        self._permission_type_ids = view_event_type_ids

    def has_permission(self, permission, event_type_id=None):
        if permission is "view-event-type":
            if event_type_id in self._permission_type_ids:
                return True
            elif "view-all-event-types" in self._permissions:
                return True
            return False
        elif permission in self._permissions:
            return True
        return False

    def __str__(self):
        output = {"user_id": self.user_id,
                  "email_address": self.email_address,
                  "session_token": self.session_token,
                  "permissions": self._permissions,
                  "view_event_type_ids": self._permission_type_ids,
                  "full_name": self.full_name}
        return json.dumps(output)
