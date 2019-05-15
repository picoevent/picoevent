from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urljoin
from json import JSONDecodeError
import json
import ssl
import logging
import sys
import re
import time

MAX_ATTEMPTS = 3
DEFAULT_LOG_FILE = "/tmp/PicoEventRestClient.log"
DEFAULT_ENDPOINT = "http://localhost/api"
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
DEFAULT_USER_AGENT += '(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
API_KEY_REGEX = re.compile("[A-F0-9]{16}")
EVENT_ID_REGEX = re.compile("[0-9]{1,5}")


def setup_file_logging(path=DEFAULT_LOG_FILE):
    logger = logging.getLogger("PicoEventRestClient")
    logger.setLevel(logging.INFO)
    # create file handler
    fh = logging.FileHandler(path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add the handler to the logger
    logger.addHandler(fh)

    logger.info("PicoEventRestClient: startup")
    return logger


class PicoEventRestClient:
    def __init__(self, endpoint, api_key, logger=None, user_agent=None):
        self._endpoint = endpoint
        self._api_key = api_key
        if user_agent:
            self._user_agent = user_agent
        else:
            self._user_agent = DEFAULT_USER_AGENT
        if logger:
            self._logger = logger
        else:
            self._logger = setup_file_logging()

    def post_event(self, e_type_id: int, e_data: dict, user_id: int = None) -> bool:
        request_obj = {"event_type_id": e_type_id,
                       "user_id": user_id,
                       "event_data": e_data}
        request_bytes = json.dumps(request_obj).encode('utf-8')

        ssl_context = ssl.SSLContext()
        ssl_context.load_default_certs()

        request_url = urljoin(self._endpoint, self._api_key)

        req = Request(request_url,
                      data=request_bytes,
                      headers={'Content-Type': 'application/json',
                               'User-Agent': self._user_agent},
                      method="POST")

        attempts_remaining = MAX_ATTEMPTS
        while attempts_remaining > 0:
            try:
                response = urlopen(req, context=ssl_context)
                json_data = json.loads(response.read())
                if json_data["success"]:
                    if self._logger:
                        self._logger.info("Posted event to PicoEvent service.")
                    return True
                else:
                    if self._logger:
                        error_msg = json_data["error"]
                        self._logger.error("PicoEvent: " + error_msg)
                    return False
            except URLError as err:
                attempts_remaining -= 1
                if self._logger:
                    self._logger.error("URLError: {0}. Retrying, {1} attempts remaining.".format(err,
                                                                                                 attempts_remaining))

    def get_event_types(self):
        ssl_context = ssl.SSLContext()
        ssl_context.load_default_certs()
        request_url = urljoin(self._endpoint + "/list-event-types/", self._api_key)

        req = Request(request_url,
                      headers={'Content-Type': 'application/json',
                               'User-Agent': self._user_agent},
                      method="GET")

        attempts_remaining = MAX_ATTEMPTS
        while attempts_remaining > 0:
            try:
                response = urlopen(req, context=ssl_context)
                json_data = json.loads(response.read())
                if json_data["success"]:
                    if self._logger:
                        self._logger.info("Received event types from PicoEvent service.")
                    event_types = json_data["event_types"]
                    return event_types
                else:
                    if self._logger:
                        error_msg = json_data["error"]
                        self._logger.error("PicoEvent: " + error_msg)
                    return False
            except URLError as err:
                attempts_remaining -= 1
                if self._logger:
                    self._logger.error("URLError: {0}. Retrying, {1} attempts remaining.".format(err,
                                                                                                 attempts_remaining))

    def test_stream(self, seconds: int = None):
        stop_time = None
        if seconds:
            stop_time = time.time() + seconds

        gas_price = 4000
        largest_block = 500
        x = 1

        while 1:
            test_object = {"gasPrice": gas_price,
                           "latestBlock": largest_block,
                           "counter": x}

            if self.post_event(1, test_object):
                self._logger.info("Event posted to REST endpoint successfully. (counter={0})".format(x))
            else:
                self._logger.info("Event post failed. (counter={0}".format(x))

            gas_price += 1
            largest_block += 1
            x += 1

            if stop_time:
                if time.time() > stop_time:
                    break


HELP = """
python3 PicoEventRestClient.py <command> <args> <endpoint>

commands:
list-event-types (args: api_key, list all available event types and ids)
test (args: api_key seconds or 'forever' to loop a stress test)
post (args: api_key event_type_id event_data.json filepath)

examples:

python3 PicoEventRestClient.py list-event-types 8994995B8FDB3651 <endpoint>
\tLists all available event types in JSON format

python3 PicoEventRestClient.py test 8994995B8FDB3651 3600 <endpoint>
\tStress tests the endpoint for 3600 seconds

python3 PicoEventRestClient.py test 8994995B8FDB3651 forever <endpoint>
\tLoops the stress test

python3 PicoEventRestClient.py post 8994995B8FDB3651 5 <endpoint>
\tAttempts to parse valid JSON data from stdin to post to the endpoint as event_type_id 5

All output is in JSON format. If endpoint is not provided, the default is http://localhost/api
"""

VALID_COMMANDS = {"list-event-types", "test", "post"}

if __name__ == "__main__":
    logger = setup_file_logging()
    argc = len(sys.argv)
    if argc < 3:
        logger.error("Invalid command line arguments.")
        print(HELP)
        sys.exit(0)
    else:
        command = sys.argv[1]
        if command not in VALID_COMMANDS:
            logger.error("{0} not a valid command.".format(command))
            print(HELP)
            sys.exit()
        elif command == "list-event-types":
            api_key = sys.argv[2]
            if API_KEY_REGEX.match(api_key):
                if argc > 3:
                    endpoint = sys.argv[3]
                else:
                    endpoint = DEFAULT_ENDPOINT
                logger.info("Initializing PicoEventRestClient.py using API key {0} and endpoint {1}".format(api_key,
                                                                                                            endpoint))
                rest_client = PicoEventRestClient(endpoint, api_key, logger)
                event_types_data = rest_client.get_event_types()
                if event_types_data:
                    output = {"success": True,
                              "event_types": event_types_data}
                    sys.stdout.write(json.dumps(output))
                    sys.exit(0)
                else:
                    output = {"success": False,
                              "error_message": "Request failed, check the log file for additional info."}
                    sys.stdout.write(json.dumps(output))
                    sys.exit(1)
            else:
                logger.error("Invalid API key, failed regex check: {0}".format(api_key))
                output = {"success": False,
                          "error_message": "Invalid API key."}
                sys.stdout.write(json.dumps(output))
                sys.exit(1)
        elif command == "test":
            api_key = sys.argv[2]
            if API_KEY_REGEX.match(api_key):
                test_time = None
                if argc > 3:
                    test_time = int(sys.argv[3])
                if argc > 4:
                    endpoint = sys.argv[4]
                else:
                    endpoint = DEFAULT_ENDPOINT

                # create console handler with a higher log level
                ch = logging.StreamHandler()
                ch.setLevel(logging.DEBUG)
                # create formatter and add it to the handlers
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                ch.setFormatter(formatter)
                # add the handlers to the logger
                logger.addHandler(ch)

                rest_client = PicoEventRestClient(endpoint, api_key, logger)
                rest_client.test_stream(test_time)
        elif command == "post":
            api_key = sys.argv[2]
            if API_KEY_REGEX.match(api_key):
                if argc > 3:
                    event_type_id = sys.argv[3]
                    if EVENT_ID_REGEX.match(event_type_id):
                        event_type_id = int(event_type_id)
                        if argc > 4:
                            endpoint = sys.argv[4]
                        else:
                            endpoint = DEFAULT_ENDPOINT
                        try:
                            event_data = json.load(sys.stdin)
                            logger.info("Initializing PicoEventClient with API key {0} using endpoint {1}".format(
                                api_key,
                                endpoint))
                            rest_client = PicoEventRestClient(endpoint, api_key, logger)
                            response = rest_client.post_event(event_type_id, event_data)
                        except JSONDecodeError:
                            logger.error(
                                "JSONDecodeError exception thrown on data piped into stdin.")
                            output = {"success": False,
                                      "error_message": "Request failed, check the log file for additional info."}
                            sys.stdout.write(json.dumps(output))
                            sys.exit(1)
                    else:
                        logger.error(
                            "Invalid post command format, run PicoEventRestClient.py with no args to see help.")
                        output = {"success": False,
                                  "error_message": "Request failed, check the log file for additional info."}
                        sys.stdout.write(json.dumps(output))
                        sys.exit(1)
                else:
                    logger.error("Invalid post command format, run PicoEventRestClient.py with no args to see help.")
                    output = {"success": False,
                              "error_message": "Request failed, check the log file for additional info."}
                    sys.stdout.write(json.dumps(output))
                    sys.exit(1)
