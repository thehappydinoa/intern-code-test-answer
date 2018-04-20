#!/usr/bin/env python3.6
import json
import unittest
import requests
from psycopg2 import connect, OperationalError, ProgrammingError, InternalError

from settings import config

try:
    conn = connect(host=config["db_config"]["host"], dbname=config["db_config"]["dbname"],
                   user=config["db_config"]["user"], password=config["db_config"]["password"])
except OperationalError as e:
    print(str(e))
    exit(1)


def psql_command(command, input=False, fetch=True, fetchall=False):
    cur = conn.cursor()
    try:
        cur.execute(command)
        if fetch:
            if fetchall:
                response = cur.fetchall()
            else:
                response = cur.fetchone()
        else:
            response = None
    except (ProgrammingError, InternalError) as e:
        response = None
    conn.commit()
    cur.close()
    return response


def iso8601(time):
    return time.replace(tzinfo=timezone.utc).isoformat()[:-9] + 'Z'


def serializeItem(item):
    if item:
        return {'item': {
            'id': item[0],
            'title': item[1],
            'categoryId': item[2],
            'createdAt': iso8601(item[3]),
            'updatedAt': iso8601(item[4])
        }}


def add_item():
    item = {"item": {
        "title": "some title",
        "categoryId": 1
    }}
    title = item["item"]["title"]
    categoryId = item["item"]["categoryId"]
    response = psql_command(
        "INSERT INTO items(title, category_id) VALUES(%s, %s) returning *;", input=(title, categoryId))
    return serializeItem(response)


def get_items():
    response = psql_command("SELECT * FROM items;", fetchall=True)
    itemsList = []
    for item in response:
        itemsList.append(serializeItem(item)['item'])
    result = {"items": itemsList}
    return result


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:" + str(config["port"])

    def test_get_index(self):
        psql_command('TRUNCATE items RESTART IDENTITY', fetch=False)
        r = requests.get(self.base_url + '/')
        assert 'OK' in r.json()['status']

    def test_get_items(self):
        item1 = add_item()
        item2 = add_item()
        expected = json.dumps(get_items())
        r = requests.get(self.base_url + '/items')
        assert expected in r.text

    def test_get_make(self):
        item3 = add_item()
        expected = json.dumps(item3)
        r = requests.get(self.base_url + '/items/' + item3["item"]["id"])
        assert expected in r.text


if __name__ == '__main__':
    unittest.main()
