# Intern Code Test Response [![Python 2.7](https://img.shields.io/badge/Python-2%20&%203-blue.svg)](https://www.python.org/download/)

Response to [Intern Code Test](https://github.com/uprightlabs/intern-code-test)

## How to run

1.  Configure database settings in `settings.py`

    ```json
    "db_config": {
        "host": "localhost",
        "dbname": "code-test",
        "user": "intern",
        "password": "password101"
    }
    ```

2.  Install requirements

    ```bash
    pip install -r requirements.txt
    ```

3.  Run `app.py`

    ```bash
    python app.py
    ```

    Should print:

    ```bash
    127.0.0.1 - - [00/Apr/2018 09:00:00] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "POST /items HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "PUT /items/3 HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "GET /items/2 HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "DELETE /items/5 HTTP/1.1" 200 -
    127.0.0.1 - - [00/Apr/2018 09:00:00] "GET /items HTTP/1.1" 200 -
    ```

## DEPENDENCIES

This has been tested with Python 2.7 and 3.6.

## LICENSE

MIT License
