from datetime import datetime
import json


class DjangoUser:
    user_id: int
    username: str
    first_name: str
    last_name: str
    email_address: str
    last_logged_in: datetime
    created: datetime

    def __init__(self, user_id, username, first_name, last_name,
                 email_address, last_logged_in, created):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.last_logged_in = last_logged_in
        self.created = created

    def __str__(self):
        output = {"user_id": self.user_id,
                  "username": self.username,
                  "first_name": self.first_name,
                  "last_name": self.last_name,
                  "email_address": self.email_address,
                  "last_logged_in": self.last_logged_in.isoformat(),
                  "created": self.created.isoformat()}
        return json.dumps(output)
