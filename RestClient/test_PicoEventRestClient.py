# This assumes Flask is running on localhost port 5000

from PicoEvent.Database import Database
from PicoEvent.EventLog import EventLog
from PicoEvent.Environment import Environment
import RestClient.PicoEventRestClient
import unittest
import binascii
import os

TEST_ENDPOINT = "http://localhost:5000/api"


class TestListEventTypes(unittest.TestCase):
    def setUp(self) -> None:
        # my default development environment values
        dev = Environment("localhost", "localhost", "pico", "password", "picoevent", "picoevent_test_db", 1000, 3600,
                          "localhost", "localhost")
        self._db = Database(env=dev)
        self._event_log = EventLog(self._db)
        self._event_type_ids = self._event_log.list_event_types()

    def test_listUnitTypes(self):
        new_api_key = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
        result = self._db.create_api_key(new_api_key, rate_limit_quota=15000, next_reset_seconds=5000)
        self.assertGreater(result, 0)
        rest_client = PicoEventRestClient.PicoEventRestClient(TEST_ENDPOINT, new_api_key)
        retrieved_event_types = rest_client.get_event_types()
        self.assertEqual(len(retrieved_event_types), len(self._event_type_ids))
        for x in range(0,len(retrieved_event_types)):
            event_type = self._event_type_ids[x]
            retrieved_event_type = retrieved_event_types[x]
            self.assertEqual(event_type[0], retrieved_event_type[0])
            self.assertEqual(event_type[1], retrieved_event_type[1])


if __name__ == "__main__":
    unittest.main()
