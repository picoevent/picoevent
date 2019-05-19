class Environment:
    def __init__(self, app):
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
    def db_config(self):
        return {"mysql_host": self._mysql_host,
                "mysql_read_only_host": self._mysql_read_only_host,
                "mysql_user": self._mysql_user,
                "mysql_passwd": self._mysql_passwd,
                "mysql_db": self._mysql_db,
                "mysql_test_db": self._mysql_test_db,
                "rate_limit_quota": self._rate_limit_quota,
                "rate_limit_reset": self._rate_limit_reset}

    @property
    def redis_master_host(self) -> str:
        return self._redis_master_host

    @property
    def redis_read_only_host(self) -> str:
        return self._redis_read_only_host
