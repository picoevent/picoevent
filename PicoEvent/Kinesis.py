from PicoEvent.EventLog import Event
import binascii
import json

MAX_EVENT_DATA_BYTES = 2048  # Kinesis can get expensive


# TODO: publishing to Kinesis on the roadmap for redundancy in S3 at the minimum
# also possibly subscribe functionality for some redundancy against DB failures/slowdown


class KinesisInterface:
    def __init__(self, logger=None):
        self._logger = logger

    def publish_event(self, event: Event, tag=None):
        if tag is None:
            tag = event.event_type
        kinesis_data = dict(event.event_data)
        kinesis_data["node_id"] = event.node_id
        kinesis_data["user_id"] = event.user_id
        kinesis_data["event_id"] = event.event_id
        kinesis_data["event_type_id"] = event.event_type_id

        base64_data = binascii.b2a_base64(json.dumps(kinesis_data))
        if len(base64_data) > MAX_EVENT_DATA_BYTES:
            self._logger.error(
                "The Base64 encoded event data is {0} bytes exceeding the MAX_EVENT_DATA_BYTE limit of {1}".format(
                    len(base64_data), MAX_EVENT_DATA_BYTES
                ))
            self._logger.info("You can change MAX_EVENT_DATA_BYTES to any value up to the DBMS max (4GB for MySQL)")
            return False
        self._logger.info("Published event to Kinesis stream tagged {0}".format(tag))
        return True
