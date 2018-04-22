#!/usr/bin/env python
from json import loads, dumps
from datetime import datetime, timezone
from flask import Flask, request
from psycopg2 import connect, ProgrammingError, OperationalError, InternalError

# Gets config from settings.py
from settings import config

# Creates Flask app from config
app = Flask(__name__)
app.debug = config["debug"]
app.secret_key = config["secret_key"]

# Try to connect to DB using db_config
# Catches OperationalErrors (Auth Errors and Database Existence)
try:
    conn = connect(
        host=config["db_config"]["host"],
        dbname=config["db_config"]["dbname"],
        user=config["db_config"]["user"],
        password=config["db_config"]["password"])
except OperationalError as e:
    print(str(e))
    exit(1)


# Tries to return results of string `command`
# Catches ProgrammingError and InternalError (Value Errors and Existence)
# Boolean `fetchall` describes how many responses are expected
def psql_command(command, values=False, fetchall=False):
    if not command.endswith(';'):
        command += ';'
    cur = conn.cursor()
    try:
        if values and not ';' in str(values):
            cur.execute(command, values)
        else:
            cur.execute(command)
        if fetchall:
            response = cur.fetchall()
        else:
            response = cur.fetchone()
    except (ProgrammingError, InternalError) as e:
        print(str(e))
        response = None
    conn.commit()
    cur.close()
    return response


# Returns string that describes the time in ISO8601 UTC
def iso8601(time):
    return time.replace(tzinfo=timezone.utc).isoformat()[:-9] + 'Z'


# Returns array that describes the tuple 'item'
def serializeItem(item):
    if item:
        return {
            'item': {
                'id': item[0],
                'title': item[1],
                'categoryId': item[2],
                'createdAt': iso8601(item[3]),
                'updatedAt': iso8601(item[4])
            }
        }


# Returns array of all items in table `items`
@app.route('/items', methods=['GET'])
def get_items():
    response = psql_command("SELECT * FROM items;", fetchall=True)
    itemsList = []
    for item in response:
        itemsList.append(serializeItem(item)['item'])
    result = {"items": itemsList}
    return dumps(result), 200


# Tries to return a serialized json object of the item with the id of string 'item_id'
# Catches IndexError (Value Errors and Existence)
@app.route('/items/<string:item_id>', methods=['GET'])
def get_item(item_id):
    response = psql_command(
        "SELECT * FROM items WHERE ID = %s;", values=(item_id, ))
    try:
        result = serializeItem(response)
        return dumps(result)
    except IndexError:
        return None, 404


# Creates and returns a serialized json object of the item created
@app.route('/items', methods=['POST'])
def add_item():
    item = loads(request.data)
    title = item["item"]["title"]
    categoryId = item["item"]["categoryId"]
    response = psql_command(
        "INSERT INTO items(title, category_id) VALUES(%s, %s) returning *;",
        values=(title, categoryId))
    return dumps(serializeItem(response)), 201


# Edits and returns a serialized json object of the item updated
@app.route('/items/<string:item_id>', methods=['PUT'])
def edit_item(item_id):
    title = loads(request.data)["item"]["title"]
    updated_at = datetime.utcnow().isoformat()
    response = psql_command(
        "UPDATE items SET title = %s, updated_at = %s WHERE ID = %s returning *;",
        values=(title, updated_at, item_id))
    return dumps(serializeItem(response)), 200


# Tries to delete the item with id of string 'item_id' and returns {}
# Catches Exception (Value Errors and Existence)
@app.route('/items/<string:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        psql_command(
            "DELETE FROM items WHERE id = %s returning *;", values=(item_id, ))
        result = {}
        return dumps(result), 200
    except Exception as e:
        print("Failed Delete")
        print(str(e))
        return None, 404


# Handles 404 errors
@app.errorhandler(404)
def error_404(error):
    return dumps({"error": str(error)}), 404


# Handles index route
@app.route("/")
def index():
    return dumps({'status': 'OK'}), 200


# Runs flask app object 'app'
if __name__ == '__main__':
    app.run(port=config["port"])
