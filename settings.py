from os import urandom

config = {
    "port": 3000,
    "debug": True,
    "secret_key": urandom(24),
    "db_config": {
        "host": "localhost",
        "dbname": "code-test",
        "user": "intern",
        "password": "password101"
    }
}
