from PicoEvent.SecureStorage import SecureDatabase
from PicoEvent.Environment import EnvironmentBase
import os
import json
import unittest
import logging

logger = logging.getLogger("PicoEvent.SecureStorage_unittest")
logger.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


class TestEncryptData(unittest.TestCase):
    def setUp(self) -> None:
        config_stream = open("config/config.json")
        _config = json.load(config_stream)
        config_stream.close()
        env = EnvironmentBase()
        env._mysql_host = _config["mysql_host"]
        env._mysql_read_only_host = _config["mysql_host"]
        env._mysql_user = _config["mysql_user"]
        env._mysql_passwd = _config["mysql_passwd"]
        env._mysql_db = _config["mysql_db"]
        env._mysql_test_db = _config["mysql_test_db"]
        env.secret_key = os.urandom(16)
        self.secure_db = SecureDatabase(env, logger, True)
        self.mock_object = {"AWSSecretKey": "ABADFGF#$QT%#%#HQ", "PayPalSecretKey": "AABASFADFADIASDF"}

    def test_encrypt_data(self):
        last_row_id = self.secure_db.encrypt_json_serializable_object(self.mock_object, 1, 1)
        self.assertGreater(last_row_id, 0)
        decrypted_data = self.secure_db.decrypt_json_serializable_object(last_row_id)
        self.assertEqual(decrypted_data.secure_storage_id, last_row_id)


class TestDecryptData(unittest.TestCase):
    def setUp(self) -> None:
        config_stream = open("config/config.json")
        _config = json.load(config_stream)
        config_stream.close()
        env = EnvironmentBase()
        env._mysql_host = _config["mysql_host"]
        env._mysql_read_only_host = _config["mysql_host"]
        env._mysql_user = _config["mysql_user"]
        env._mysql_passwd = _config["mysql_passwd"]
        env._mysql_db = _config["mysql_db"]
        env._mysql_test_db = _config["mysql_test_db"]
        env.secret_key = os.urandom(16)
        self.secure_db = SecureDatabase(env, logger, True)
        self.mock_object = {"AWSSecretKey": "ABADFGF#$QT%#%#HQ", "PayPalSecretKey": "AABASFADFADIASDF"}

    def test_decrypt_data(self):
        last_row_id = self.secure_db.encrypt_json_serializable_object(self.mock_object, 1, 1)
        self.assertGreater(last_row_id, 0)
        decrypted_data = self.secure_db.decrypt_json_serializable_object(last_row_id)
        self.assertEqual(decrypted_data.secure_storage_id, last_row_id)
        self.assertEqual(decrypted_data.json_data_object["AWSSecretKey"], self.mock_object["AWSSecretKey"])


if __name__ == "__main__":
    unittest.main()
