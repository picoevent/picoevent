# Database Configuration

If you simply want to develop instead of directly deploying to an instance, this is a simplified guide to setting up the database.

Create a MySQL database, you should also create a separate test db to run unittests.

Create a user to access the database, GRANT ALL to this user since it will be installing the schema.
Be sure 

**Test the new user using MySQL client**

You're going to need the mysqlclient Python library at the very least to setup your database, so go ahead and create a virtual
environment.

`$ python3.6 -m venv venv`

`$ . ./venv/bin/activate `

**Set the PYTHONPATH environmental variable your current working directory.**

`(venv) export PYTHONPATH=/home/django/picoevent`

Run PicoEvent/Database.py to setup your schema.

`(venv) python PicoEvent/Database.py`

At this point you should be able to use the ConsoleUserManagement.py tool in
