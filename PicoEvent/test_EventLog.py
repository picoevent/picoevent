from PicoEvent.Database import Database, DEFAULT_EVENTS
from PicoEvent.EventLog import EventLog, EventLogException
import unittest
import logging

logger = logging.getLogger("PicoEvent.EventLog_unittest")
logger.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


class TestAddingEventCacheClearing(unittest.TestCase):
    def setUp(self):
        self._db = Database(logger, True)
        self._event_log = EventLog(self._db, logger)
        self._added_events = []
        x = 0
        for each_event in DEFAULT_EVENTS:
            event_type_id = self._event_log.add_event_type(each_event)
            self.assertGreater(event_type_id, 0)
            self._added_events.append(each_event)
            if x == 4:
                break
            x += 1

    def test_add_event_cache_clearing(self):
        remaining_events = DEFAULT_EVENTS - set(self._added_events)
        for each_event in remaining_events:
            event_type_id = self._event_log.add_event_type(each_event)
            self.assertGreater(event_type_id, 0)
            self._added_events.append(each_event)
        self.assertSetEqual(set(self._added_events), DEFAULT_EVENTS)
        not_found = False
        try:
            for each_event in self._event_log.list_event_types():
                if each_event[1] not in DEFAULT_EVENTS:
                    not_found = True
                    break
        except EventLogException:
            self.fail("Event log exception")
        self.assertFalse(not_found)


if __name__ == "__main__":
    unittest.main()
