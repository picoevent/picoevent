from PicoEvent.Database import Database, DatabaseNotFoundException
from PicoEvent.EventLog import Event
import unittest
import os
import binascii
import logging
import random
from datetime import datetime, timedelta

DEFAULT_EVENTS = ["Create API Key",
                  "Change Quota",
                  "Manual Reset",
                  "Suspend API Key",
                  "Add Permission",
                  "Create Analyst User",
                  "Remove Permission",
                  "Add Event Type"]

logger = logging.getLogger("PicoEvent.Database_unittest")
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


def deserialize_iso_format(iso_datetime: str) -> datetime:
    return datetime.strptime(iso_datetime, "%Y-%m-%dT%H:%M:%S%z")


def random_later_datetime(max_seconds=3600):
    delta = timedelta(seconds=random.randint(0, max_seconds))
    return datetime.now() + delta


class TestDatabaseNotFoundException(unittest.TestCase):
    MAX_EVENTS_LOGGED = 1000

    def setUp(self) -> None:
        self._db = Database(logger, True)
        self._mock_data = dict()
        total_events = random.randint(0, self.MAX_EVENTS_LOGGED)

        for each in DEFAULT_EVENTS:
            event_type_id = self._db.create_event_type(each)
            self.assertGreater(event_type_id, 0, msg="Failed to create event type")
            mock_events = []
            now = datetime.now()
            for x in range(0, total_events):
                mock_event_data = {"floatMock": random.random(),
                                   "datetimeMock": random_later_datetime().isoformat(),
                                   "integerMock": random.randint(0, 1500000),
                                   "stringMock": "a" * random.randint(0, 1024)}

                new_mock_event = Event(0, event_type_id, each, mock_event_data, 0, 1, now)
                mock_events.append(new_mock_event)
            self._mock_data[each] = mock_events

        event_type = random.choice(DEFAULT_EVENTS)
        mock_events = self._mock_data[event_type]
        event_type_id = None
        for each_mock in mock_events:
            if event_type_id is None:
                event_type_id = each_mock.event_type_id
            event_id = self._db.log_event(each_mock.event_data,
                                          each_mock.event_type_id,
                                          each_mock.node_id,
                                          each_mock.user_id)
            self.assertGreater(event_id, 0, msg="Failed to log event.")
            each_mock.event_id = event_id
        event_type_count = self._db.get_event_count(event_type_id=event_type_id)
        self.assertEqual(event_type_count, len(mock_events))
        logger.info("Events logged: {0} ({1})".format(event_type_count, event_type))

    def test_lookupFailed(self):
        with self.assertRaises(DatabaseNotFoundException):
            self._db.get_event_data(self.MAX_EVENTS_LOGGED + self.MAX_EVENTS_LOGGED)


class TestEventTypeIdLogging(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)
        self._mock_data = dict()
        now = datetime.now()
        for each in DEFAULT_EVENTS:
            event_type_id = self._db.create_event_type(each)
            self.assertGreater(event_type_id, 0, msg="Failed to create event type")
            mock_events = []
            for x in range(0, random.randint(10, 50)):
                mock_event_data = {"floatMock": random.random(),
                                   "datetimeMock": random_later_datetime().isoformat(),
                                   "integerMock": random.randint(0, 1500000),
                                   "stringMock": "a" * random.randint(0, 1024)}

                new_mock_event = Event(0, event_type_id, each, mock_event_data, 0, 1, now)
                mock_events.append(new_mock_event)
            self._mock_data[each] = mock_events

    def test_logging(self):
        total_events_logged = 0
        event_type = random.choice(DEFAULT_EVENTS)
        mock_events = self._mock_data[event_type]
        event_type_id = None
        for each_mock in mock_events:
            if event_type_id is None:
                event_type_id = each_mock.event_type_id
            event_id = self._db.log_event(each_mock.event_data,
                                          each_mock.event_type_id,
                                          each_mock.node_id,
                                          each_mock.user_id)
            self.assertGreater(event_id, 0, msg="Failed to log event.")
            each_mock.event_id = event_id
        event_type_count = self._db.get_event_count(event_type_id=event_type_id)
        self.assertEqual(event_type_count, len(mock_events))
        logger.info("Events logged: {0} ({1})".format(event_type_count, event_type))
        logger.info("Fetching events individually...")
        total_events_logged += event_type_count
        for each_mock in mock_events:
            db_event_data = self._db.get_event_data(each_mock.event_id)
            # DB: event_id, event_type_id, node_id, user_id, event_data, created, event_type.event_type
            self.assertEqual(db_event_data[1], each_mock.event_type_id)
            self.assertEqual(db_event_data[2], each_mock.node_id)
            self.assertEqual(db_event_data[3], each_mock.user_id)
            # db_event_data = json.loads(db_event_data[4])
            # self.assertEqual(each_mock.event_data["floatMock"], db_event_data["floatMock"])
            # self.assertEqual(db_event_data[6], each_event_type)
        logger.info("Retrieving all events of type in single query...")
        all_events_of_type = self._db.retrieve_events(event_type_id=event_type_id)
        mock_events_reversed = mock_events
        mock_events_reversed.reverse()
        # event_id, event_type_id, node_id, user_id, created
        for x in range(0, len(mock_events_reversed)):
            self.assertEqual(all_events_of_type[x][0], mock_events_reversed[x].event_id)
            self.assertEqual(all_events_of_type[x][1], mock_events_reversed[x].event_type_id)
            self.assertEqual(all_events_of_type[x][2], mock_events_reversed[x].node_id)
            self.assertEqual(all_events_of_type[x][3], mock_events_reversed[x].user_id)
        self.assertEqual(len(all_events_of_type), event_type_count)
        db_total_event_count = self._db.get_event_count()
        self.assertEqual(db_total_event_count, total_events_logged)


class TestRateLimitQuota(unittest.TestCase):
    TEST_LIMIT = 500

    def setUp(self):
        self._db = Database(logger, True)
        new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
        node_id = self._db.create_api_key(new_api_key)
        self.assertGreater(node_id, 0)
        self.api_key = new_api_key
        self.node_id = node_id

    def test_rateLimit(self):
        for x in range(0, self.TEST_LIMIT):
            self.assertTrue(self._db.update_quota(self.node_id))
        node_info = self._db.validate_api_key(self.api_key)
        self.assertEqual(node_info[0], self.node_id)
        self.assertEqual(node_info[4], self.TEST_LIMIT)
        next_reset = self._db.next_quota_reset
        self.assertTrue(self._db.reset_quota(self.node_id, next_reset))
        node_info = self._db.validate_api_key(self.api_key)
        self.assertEqual(node_info[0], self.node_id)
        self.assertEqual(0, node_info[4])


class TestListEventTypes(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)
        for each in DEFAULT_EVENTS:
            self._db.create_event_type(each)

    def test_list_event_types(self):
        event_types = self._db.list_event_types()
        all_events = []
        for event in event_types:
            all_events.append(event[1])
        result = set(DEFAULT_EVENTS) - set(all_events)
        self.assertEqual(0, len(result))


class TestCreateEventType(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)

    def test_create_event_type(self):
        result = self._db.create_event_type("Node Update Event")
        self.assertGreater(result, 0)

    def test_create_event_type_db_fault(self):
        result = self._db.create_event_type("a" * 60)
        self.assertEqual(-1, result)


class TestAdminLogin(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)

    def test_admin_login(self):
        result = self._db.login("admin", "test_password")
        self.assertIsNotNone(result)
        new_session_token = result[0]
        admin_user_id = result[1]
        admin_user = self._db.validate_session(new_session_token)
        self.assertEqual(admin_user.user_id, admin_user_id)
        self.assertEqual(admin_user.session_token, new_session_token)
        self.assertEqual(admin_user.email_address, "admin")
        self.assertEqual(admin_user.full_name, "Administrator")


class TestListAPIKeys(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)
        self._target_api_keys = random.randint(5, 100)
        self._api_keys = []
        for x in range(0, self._target_api_keys):
            new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
            result = self._db.create_api_key(new_api_key)
            self.assertGreater(result, 0)
            self._api_keys.append(new_api_key)

    def test_list_api_keys(self):
        all_api_keys = self._db.list_api_keys()
        self.assertEqual(self._target_api_keys, len(all_api_keys))
        for x in range(0, self._target_api_keys):
            self.assertEqual(all_api_keys[x][1], self._api_keys[x])


class TestCreateAPIKey(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)

    def test_add_key(self):
        new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
        result = self._db.create_api_key(new_api_key)
        self.assertGreater(result, 0)

    def test_invalid_api_key(self):
        result = self._db.create_api_key("invalid")
        self.assertEqual(result, -1)

    def test_custom_reset_interval(self):
        new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
        result = self._db.create_api_key(new_api_key, next_reset_seconds=5000)
        self.assertGreater(result, 0)
        api_key_info = self._db.validate_api_key(new_api_key)
        lower_bounds = 4995
        higher_bounds = 5005
        self.assertGreater(api_key_info[3], datetime.now() + timedelta(seconds=lower_bounds))
        self.assertLess(api_key_info[3], datetime.now() + timedelta(seconds=higher_bounds))
        self.assertEqual(result, api_key_info[0])


if __name__ == "__main__":
    unittest.main()
