# callable from another process using a subprocess type function in any language that supports it
# Python 3.6 programs should just use PicoEventRestClient.py directly as there are no external dependencies
# This hasn't really been tested at all

from RestClient.PicoEventRestClient import PicoEventRestClient, API_KEY_REGEX, DEFAULT_ENDPOINT, EVENT_ID_REGEX
from json import JSONDecodeError
import logging
import sys
import json


def setup_file_logging(path=DEFAULT_LOG_FILE):
    logger = logging.getLogger("ExternalPicoEventRestClient")
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
        print(help)
        sys.exit(0)
    else:
        command = sys.argv[1]
        if command not in VALID_COMMANDS:
            logger.error("{0} not a valid command.".format(command))
            print(help)
            sys.exit()
        elif command is "list_event_types":
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
        elif command is "test":
            logger.info("Attempted to run test command, not yet implemented.")
        elif command is "post":
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
                            response = rest_client.post_event(event_type_id, event_data, None)
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
