class Environment:
    def __init__(self, mysql_host: str, mysql_read_only_host: str, mysql_user: str, mysql_password: str, mysql_db: str,
                 mysql_test_db: str, rate_limit_quota: int, rate_limit_reset: int,
                 redis_master_host: str, redis_read_only_host: str):
        self._mysql_host = mysql_host
        self._mysql_read_only_host = mysql_read_only_host
        self._mysql_user = mysql_user
        self._mysql_passwd = mysql_password
        self._mysql_db = mysql_db
        self._mysql_test_db = mysql_test_db
        self._rate_limit_quota = rate_limit_quota  # Default is 1000 requests/per API key
        self._rate_limit_reset = rate_limit_reset  # Default is 3600 seconds so that is 1000 requests per hour
        self._redis_master_host = redis_master_host
        self._redis_read_only_host = redis_read_only_host

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
