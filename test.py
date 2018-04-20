#!/usr/bin/env python3.6
import json
import unittest
import requests
from datetime import datetime, timezone
from psycopg2 import connect, OperationalError, ProgrammingError, InternalError

from settings import config

try:
    conn = connect(host=config["db_config"]["host"], dbname=config["db_config"]["dbname"],
                   user=config["db_config"]["user"], password=config["db_config"]["password"])
except OperationalError as e:
    print(str(e))
    exit(1)


def psql_command(command, values=False, fetch=True, fetchall=False):
    if not command.endswith(';'):
        command = command + ';'
    cur = conn.cursor()
    try:
        if values:
            if not ';' in str(values):
                cur.execute(command, values)
            else:
                raise InternalError("SQL Injection attempt")
        else:
            cur.execute(command)
        if fetch:
            if fetchall:
                response = cur.fetchall()
            else:
                response = cur.fetchone()
        else:
            response = None
    except (ProgrammingError, InternalError) as e:
        print(str(e))
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
        "INSERT INTO items(title, category_id) VALUES(%s, %s) returning *;", values=(title, categoryId))
    return serializeItem(response)


def get_items():
    response = psql_command("SELECT * FROM items;", fetchall=True)
    itemsList = []
    for item in response:
        itemsList.append(serializeItem(item)['item'])
    result = {"items": itemsList}
    return result


def get_item(item_id):
    response = psql_command(
        "SELECT * FROM items WHERE ID = %s;", values=(item_id,))
    try:
        result = serializeItem(response)
        return json.dumps(result)
    except IndexError:
        result = None
        return result


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:" + str(config["port"])
        psql_command('TRUNCATE items RESTART IDENTITY', fetch=False)

    def test_get_index(self):
        r = requests.get(self.base_url + '/')
        assert str(r.status_code) in "200"
        assert 'OK' in r.json()['status']

    def test_get_items(self):
        item1 = add_item()
        item2 = add_item()
        expected = json.dumps(get_items())
        r = requests.get(self.base_url + '/items')
        assert str(r.status_code) in "200"
        assert expected in r.text

    def test_get_item(self):
        item3 = add_item()
        expected = json.dumps(item3)
        r = requests.get(self.base_url + '/items/' + str(item3["item"]["id"]))
        assert str(r.status_code) in "200"
        assert expected in r.text

    def test_post_items(self):
        item = {
            "item": {
                "title": 'Some new title here',
                "categoryId": 2
            }
        }
        r = requests.post(self.base_url + '/items', data=json.dumps(item))
        expected = get_item(r.json()["item"]["id"])
        assert str(r.status_code) in "200"
        assert expected in r.text

    def test_put_item(self):
        item = {"item": {"title": 'new title'}}
        item4 = add_item()
        expected = item["item"]["title"]
        r = requests.put(self.base_url + '/items/' +
                         str(item4["item"]["id"]), data=json.dumps(item))
        assert str(r.status_code) in "200"
        assert expected in r.json()["item"]["title"]

    def test_delete_item(self):
        item5 = add_item()
        r = requests.delete(self.base_url + '/items/' +
                            str(item5["item"]["id"]))
        response = psql_command(
            'select exists(select 1 from items where id=%s)', values=(item5["item"]["id"],))
        assert str(r.status_code) in "200"
        assert "{}" in r.text
        assert None not in response


if __name__ == '__main__':
    unittest.main()
