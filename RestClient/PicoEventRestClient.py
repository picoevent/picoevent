from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urljoin
import json
import ssl
import re

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_ENDPOINT = "http://localhost/api"
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
DEFAULT_USER_AGENT += '(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
API_KEY_REGEX = re.compile("[A-F0-9]{16}")
EVENT_ID_REGEX = re.compile("[0-9]{1,5}")


class PicoEventRestClientException(Exception):
    """ Error occurred while making a REST request to PicoEvent """
    pass


class PicoEventRestClient:
    def __init__(self, endpoint: str, api_key: str, max_attempts: int=None, logger=None, user_agent: str=None):
        self._endpoint = endpoint
        self._api_key = api_key
        if max_attempts:
            self._max_attempts = max_attempts
        else:
            self._max_attempts = DEFAULT_MAX_ATTEMPTS
        if user_agent:
            self._user_agent = user_agent
        else:
            self._user_agent = DEFAULT_USER_AGENT
        self._logger = logger

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

        attempts_remaining = self._max_attempts
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
                    raise PicoEventRestClientException
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

        attempts_remaining = self._max_attempts
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
                    raise PicoEventRestClientException
            except URLError as err:
                attempts_remaining -= 1
                if self._logger:
                    self._logger.error("URLError: {0}. Retrying, {1} attempts remaining.".format(err,
                                                                                                 attempts_remaining))