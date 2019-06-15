# This is just like Database.py except everything is encrypted using Flask's secret key
# only way we can do open source without getting our cloud abused by leaking credentials.

from Crypto.Cipher import AES
import os
from PicoEvent.Environment import EnvironmentBase
from MySQLdb import connect, Error
import binascii
import json
import logging
from json import JSONDecodeError


class DecryptedData:
    json_data_object: object
    owner_id: int
    category_id: int
    secure_storage_id: int

    def __init__(self, json_data_obj, owner_id, category_id, secure_storage_id):
        self.json_data_object = json_data_obj
        self.owner_id = owner_id
        self.secure_storage_id = secure_storage_id
        self.category_id = category_id


class SecureDatabaseException(Exception):
    """ Some sort of error with storing encrypted data """
    pass


class SecureDatabaseDeleted(SecureDatabaseException):
    """ Data we were retrieving was marked deleted..."""
    pass


class SecureDatabase:
    CATEGORIES = {1: "AWS_Credentials"}

    def __init__(self, env: EnvironmentBase, logger=None, test=False):
        self._env = env

        if logger:
            self._logger = logger
        else:
            self._logger = self._setup_file_logging("/tmp/picoevent_secure_storage.log")

        if test:
            db_name = self._env.db_config["mysql_test_db"]
        else:
            self._env = env
            db_name = self._env.db_config["mysql_db"]
        self._db_connection = connect(self._env.db_config["mysql_host"],
                                      self._env.db_config["mysql_user"],
                                      self._env.db_config["mysql_passwd"],
                                      db_name)
        if test:
            sql = "DELETE FROM secure_storage;"
            c = self._db_connection.cursor()
            c.execute(sql)
            self._db_connection.commit()

    @staticmethod
    def _setup_file_logging(log_path):
        file_logger = logging.getLogger("picoevent secure storage")
        file_logger.setLevel(logging.INFO)
        # create file handler
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add the handler to the logger
        file_logger.addHandler(fh)
        return file_logger

    def encrypt_json_serializable_object(self, json_serializable_object, owner_id: int, category_id: int):
        try:
            json_data = json.dumps(json_serializable_object)
            iv = os.urandom(16)
            hex_iv = binascii.hexlify(iv)
            cipher = AES.new(self._env.secret_key, AES.MODE_CFB, iv)
            cipher_text = cipher.encrypt(json_data)
            sql = "INSERT INTO secure_storage (owner_id,category_id,initialization_vector,encrypted_data) VALUES "
            sql += "(%s,%s,%s,%s);"
            c = self._db_connection.cursor()
            c.execute(sql, (owner_id, category_id, hex_iv, cipher_text))
            self._db_connection.commit()
            return c.lastrowid
        except Error:
            self._logger.error("Database fault.")

    def decrypt_json_serializable_object(self, row_id: int):
        try:
            c = self._db_connection.cursor()
            sql = "SELECT owner_id, category_id, initialization_vector, encrypted_data, deleted_event_id "
            sql += "FROM secure_storage WHERE id=%s"
            c.execute(sql, (row_id,))
            row = c.fetchone()
            if row[4]:
                raise SecureDatabaseDeleted
            iv = binascii.unhexlify(row[2])
            cipher = AES.new(self._env.secret_key, AES.MODE_CFB, iv)
            plain_text = cipher.decrypt(row[3])
            return DecryptedData(json.loads(plain_text), row[0], row[1], row_id)
        except JSONDecodeError:
            self._logger.error("Error deserializing JSON data: " + plain_text)
            raise JSONDecodeError
        except Error:
            self._logger.error("Database fault")
            raise SecureDatabaseException

    def destroy_secure_data(self, row_id: int, event_id: int):
        try:
            sql = "SELECT initialization_vector, encrypted_data FROM secure_storage WHERE id=%s"
            c = self._db_connection.cursor()
            c.execute(sql, (row_id,))
            row = c.fetchone()
            if row:
                new_iv = binascii.hexlify(os.urandom(16))
                overwrite_data = os.urandom(len(row[1]))
                sql = "UPDATE secure_storage SET initialization_vector=%s, encrypted_data=%s, deleted_event_id=%s "
                sql += " WHERE id=%s LIMIT 1;"
                c.execute(sql, (new_iv, overwrite_data, event_id, row_id))
                self._db_connection.commit()
                return event_id
        except Error:
            self._logger.error("Database fault.")
            raise SecureDatabaseException
