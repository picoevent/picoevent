# At around version Flask 0.8 it was much harder to read from a config file, so we sort of do the Django thing with
# a command line database initialization tool. A la manage.py. I tend to think this menu driven interface is easier
# to use, and hopefully we get something really slick after a while. That's the great thing about Python that iterative
# development.


class EnvironmentBase:
    def __init__(self):
        self._mysql_host = None
        self._mysql_read_only_host = None
        self._mysql_user = None
        self._mysql_passwd = None
        self._mysql_db = None
        self._mysql_test_db = None
        self._rate_limit_quota = None
        self._rate_limit_reset = None
        self._redis_master_host = None
        self._redis_read_only_host = None
        self.secret_key = None

    @property
    def db_config(self):
        return {"mysql_host": self._mysql_host,
                "mysql_read_only_host": self._mysql_read_only_host,
                "mysql_user": self._mysql_user,
                "mysql_passwd": self._mysql_passwd,
                "mysql_db": self._mysql_db,
                "mysql_test_db": self._mysql_test_db,
                "rate_limit_quota": self._rate_limit_quota,
                "rate_limit_reset": self._rate_limit_reset}


class Environment(EnvironmentBase):
    def __init__(self, app):
        super().__init__()
        self._mysql_host = app.config["MYSQL_HOST"]
        self._mysql_read_only_host = app.config["MYSQL_READ_ONLY_HOST"]
        self._mysql_user = app.config["MYSQL_USER"]
        self._mysql_passwd = app.config["MYSQL_PASSWORD"]
        self._mysql_db = app.config["MYSQL_DB"]
        self._mysql_test_db = app.config["MYSQL_TEST_DB"]
        self._rate_limit_quota = app.config["RATE_LIMIT_QUOTA"]
        self._rate_limit_reset = app.config["RATE_LIMIT_RESET"]
        self._redis_master_host = app.config["REDIS_MASTER_HOST"]
        self._redis_read_only_host = app.config["REDIS_READ_ONLY_HOST"]
        self.secret_key = app.config["SECRET_KEY"]

    @property
    def redis_master_host(self) -> str:
        return self._redis_master_host

    @property
    def redis_read_only_host(self) -> str:
        return self._redis_read_only_host


class ConsoleEnvironment(EnvironmentBase):
    def __init__(self):
        super().__init__()
        import json
        config_stream = open("PicoEvent/config/config.json")
        _config = json.load(config_stream)
        config_stream.close()
        self._mysql_host = _config["mysql_host"]
        self._mysql_read_only_host = self._mysql_host
        self._mysql_user = _config["mysql_user"]
        self._mysql_passwd = _config["mysql_passwd"]
        self._mysql_db = _config["mysql_db"]
        self._mysql_test_db = _config["mysql_test_db"]
        self._rate_limit_quota = 100
        self._rate_limit_reset = 3600
