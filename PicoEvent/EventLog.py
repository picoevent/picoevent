from PicoEvent.AnalystUser import AnalystUser
from PicoEvent.DjangoUser import DjangoUser
from PicoEvent.Database import Database, DEFAULT_EVENTS, DatabaseException
from PicoEvent.APIKeys import APIKey
import datetime
import json
import redis


class EventLogException(Exception):
    """ EventLog module exception """
    pass


class APIKeySuspended(EventLogException):
    """ API Key has been suspended by an analyst """
    pass


class APIKeyRateLimited(EventLogException):
    """ No more events may be logged under this API key until the quota resets """
    pass


class APIKeyInvalid(EventLogException):
    """ Invalid API key for this request """
    pass


class Event:
    event_id: int
    event_type_id: int
    event_type: str
    event_data: dict
    user_id: int
    node_id: int
    created: datetime.datetime

    def __init__(self,
                 event_id,
                 event_type_id,
                 event_type,
                 event_data,
                 user_id,
                 node_id,
                 created):
        self.event_id = event_id
        self.event_type_id = event_type_id
        self.event_type = event_type
        self.event_data = event_data
        self.user_id = user_id
        self.node_id = node_id
        self.created = created

    def is_analyst(self):
        if self.event_type in DEFAULT_EVENTS:
            return True
        return False

    def is_django_user(self):
        if self.event_type not in DEFAULT_EVENTS:
            return True
        return False

    def get_event_data(self):
        return json.dumps(self.event_data)

    def __str__(self):
        created_string = self.created
        serialize_data = {
            "event_id": self.event_id,
            "event_type_id": self.event_type_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "node_id": self.node_id,
            "user_id": self.user_id,
            "created": created_string
        }
        return json.dumps(serialize_data)


class EventLog:
    def __init__(self, db=None, logger=None):
        self._cache = redis.Redis()
        if db:
            self._db = db
        else:
            self._db = Database(logger)
        self._logger = logger

        event_types = []
        for each in self.list_event_types():
            event_types.append(each[1])
        missing_events = set(DEFAULT_EVENTS) - set(event_types)
        for new_event in missing_events:
            self._db.create_event_type(new_event)

    def deserialize_user_object(self, event: Event):
        if event.is_analyst():
            cached_user_data = self._cache.get("analyst:{0}".format(event.user_id))
            if cached_user_data:
                user_data = json.dumps(cached_user_data)
                new_analyst_user = AnalystUser(user_data["user_id"],
                                               user_data["email_address"],
                                               user_data["session_token"],
                                               user_data["full_name"],
                                               user_data["permissions"],
                                               user_data["view_event_type_ids"])
                return new_analyst_user
        else:
            cached_user_data = self._cache.get("django:{0}".format(event.user_id))
            if cached_user_data:
                user_data = json.dumps(cached_user_data)
                new_django_user = DjangoUser(user_data["user_id"],
                                             user_data["username"],
                                             user_data["first_name"],
                                             user_data["last_name"],
                                             user_data["email_address"],
                                             datetime.datetime.strptime(user_data["created"],
                                                                        "%Y-%m-%dT%H:%M:%S%z"),
                                             datetime.datetime.strptime(user_data["last_logged_in"],
                                                                        "%Y-%m-%dT%H:%M:%S%z"))
                return new_django_user

    def get_api_key_object(self, api_key: str) -> APIKey:
        try:
            node_data = self._db.validate_api_key(api_key)
            node = APIKey(node_data[0], api_key, node_data[1], node_data[2], node_data[3],
                          node_data[4], node_data[5])
            if node.suspended_event:
                raise APIKeySuspended
            if node.next_reset is None or node.next_reset < datetime.datetime.now():
                next_reset = datetime.datetime.now() + datetime.timedelta(hours=1)
                node.next_reset = next_reset
                node.events_posted = 0
                self._db.reset_quota(node.node_id, next_reset)
            if node.events_posted >= node.quota:
                raise APIKeyRateLimited
            return node
        except DatabaseException:
            raise APIKeyInvalid

    def list_api_keys(self) -> list:
        output = []
        try:
            all_api_keys = self._db.list_api_keys()
        except DatabaseException:
            raise EventLogException
        for each_api_key in all_api_keys:
            new_api_key = APIKey(each_api_key[0],
                                 each_api_key[1],
                                 each_api_key[2],
                                 each_api_key[3],
                                 each_api_key[4],
                                 each_api_key[5],
                                 each_api_key[6])
            output.append(new_api_key)
        return output

    def add_event_type(self, new_event_type):
        self._cache.delete("event_types")
        new_event_type_id = self._db.create_event_type(new_event_type)
        if new_event_type_id > 0:
            return new_event_type_id
        raise EventLogException

    @property
    def event_type_ids_as_set(self) -> set:
        try:
            all_event_types = self.list_event_types()
            all_event_type_ids = []
            for each in all_event_types:
                all_event_type_ids.append(each[0])
            return set(all_event_type_ids)
        except EventLogException:
            raise EventLogException

    def list_event_types(self) -> list:
        event_types_cached = self._cache.get("event_types")
        if event_types_cached:
            event_types = json.loads(event_types_cached)
        else:
            event_types = self._db.list_event_types()
            self._cache.set("event_types", json.dumps(event_types))
        if len(event_types) == 1 and event_types[0][0] == -1:
            raise EventLogException
        return event_types

    def get_event_count(self, user_id=None, event_type_id=None, since=None, until=None):
        return self._db.get_event_count(user_id, event_type_id, since, until)

    def log_event(self, event_data: dict, event_type_id: int, user_id: int = None, node_id: int = None):
        event_id = self._db.log_event(event_data, event_type_id, user_id, node_id)
        if event_id:
            event_type = None
            for event in self.list_event_types():
                if event[0] == event_type_id:
                    event_type = event[1]
                    break
            if not event_type:
                raise EventLogException
            new_event = Event(event_id, event_type_id, event_type, event_data, user_id, node_id,
                              datetime.datetime.now().isoformat())
            self._cache.set("event_id:{0}".format(event_id), str(new_event))
            return new_event
        raise EventLogException

    def get_event(self, event_id: int) -> Event:
        cached_event_data = self._cache.get("event_id:{0}".format(event_id))
        new_event = None
        if cached_event_data:
            cached_obj = json.loads(cached_event_data)
            new_event = Event(cached_obj["event_id"],
                              cached_obj["event_type_id"],
                              cached_obj["event_type"],
                              cached_obj["event_data"],
                              cached_obj["node_id"],
                              cached_obj["user_id"],
                              datetime.datetime.strptime(cached_obj["created"], "%Y-%m-%dT%H:%M:%S%z"))
        else:
            db_event_record = self._db.get_event_data(event_id)
            if db_event_record:
                # event_id, event_type_id, node_id, user_id, event_data, created, event_type.event_type
                new_event = Event(db_event_record[0],
                                  db_event_record[1],
                                  db_event_record[6],
                                  json.loads(db_event_record[4]),
                                  db_event_record[2],
                                  db_event_record[3],
                                  db_event_record[5])
        if new_event:
            return new_event
        else:
            raise EventLogException

    def retrieve_events(self,
                        user_id: int = None,
                        since: datetime = None,
                        until: datetime = None,
                        event_type_id: int = None,
                        node_id: int = None,
                        limit: int = 100):
        try:
            meta_data = self._db.retrieve_events(user_id, event_type_id, node_id, since, until, limit)
            #  event_id, event_type_id, node_id, user_id, created
            output = []
            for row in meta_data:
                event_id = row[0]
                cache_key = "event_id:{0}".format(event_id)
                if self._cache.exists(cache_key) is False:
                    event_data = self._db.get_event_data(event_id)
                    self._cache.set(cache_key, str(event_data))
                    output.append(event_data)
                else:
                    event_data = self._cache.get(cache_key)
                    output.append(event_data)
            return output
        except DatabaseException:
            raise EventLogException

    def update_quota(self, node: APIKey):
        try:
            self._db.update_quota(node.node_id)
        except DatabaseException:
            if self._logger:
                self._logger.error("Failed to update API rate quota for node id: {0}".format(node.node_id))
