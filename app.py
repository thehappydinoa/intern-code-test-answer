#!/usr/bin/env python
from json import loads
from datetime import datetime, timezone
from flask import Flask, request, jsonify
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
    conn = connect(host=config["db_config"]["host"], dbname=config["db_config"]["dbname"],
                   user=config["db_config"]["user"], password=config["db_config"]["password"])
except OperationalError as e:
    print(str(e))
    exit(1)

# Returns json describing the status of boolean 'status'
def status(status):
    if status:
        return jsonify({'status': 'OK'})
    return jsonify({'status': 'BAD'})

# Tries to return results of string `command`
# Catches ProgrammingError and InternalError (Value Errors and Existence)
# Boolean `fetchall` describes how many responses are expected
def psql_command(command, input=False, fetchall=False):
    if not command.endswith(';'):
        command = command + ';'
    cur = conn.cursor()
    try:
        if input:
            if not ';' in str(input):
                cur.execute(command, input)
            else:
                raise InternalError("SQL Injection attempt")
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
        return {'item': {
            'id': item[0],
            'title': item[1],
            'categoryId': item[2],
            'createdAt': iso8601(item[3]),
            'updatedAt': iso8601(item[4])
        }}


# Returns array of all items in table `items`
def get_items():
    response = psql_command("SELECT * FROM items;", fetchall=True)
    itemsList = []
    for item in response:
        itemsList.append(serializeItem(item)['item'])
    result = {"items": itemsList}
    return jsonify(result)


# Tries to return a serialized json object of the item with the id of string 'id'
# Catches IndexError (Value Errors and Existence)
def get_item(id):
    response = psql_command("SELECT * FROM items WHERE ID = %s;", input=(id,))
    try:
        result = serializeItem(response)
        return jsonify(result)
    except IndexError:
        result = status(False)
        return result


# Creates and returns a serialized json object of the item created
def add_item(item):
    item = loads(item)
    title = item["item"]["title"]
    categoryId = item["item"]["categoryId"]
    response = psql_command(
        "INSERT INTO items(title, category_id) VALUES(%s, %s) returning *;", input=(title, categoryId))
    return jsonify(serializeItem(response))


# Edits and returns a serialized json object of the item updated
def edit_item(id, data):
    title = loads(data)["item"]["title"]
    updated_at = datetime.utcnow().isoformat()
    response = psql_command(
        "UPDATE items SET title = %s, updated_at = %s WHERE ID = %s returning *;", input=(title, updated_at, id))
    return jsonify(serializeItem(response))


# Tries to delete the item with id of string 'id' and returns {}
# Catches Exception (Value Errors and Existence)
def delete_item(id):
    try:
        response = psql_command(
            "DELETE FROM items WHERE id = %s returning *;" % id)
        result = {}
        return jsonify(result)
    except Exception as e:
        print("Failed Delete")
        print(str(e))
        return status(False)


# Handles 404 errors
@app.errorhandler(404)
def error_404(error):
    return status(False), 404


# Handles index route
@app.route("/")
def index():
    return status(True)


# Handles /items route (GET and POST)
@app.route('/items', methods=['GET', 'POST'])
def items():
    if request.method == 'GET':
        return get_items()
    elif request.method == 'POST':
        response = add_item(request.data)
        return response
    return status(False)


# Handles /items/:id route (GET, POST, PUT, and DELETE)
@app.route('/items/<string:id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def items_methods(id):
    if request.method == 'GET':
        return get_item(id)
    elif request.method == 'PUT':
        return edit_item(id, request.data)
    elif request.method == 'DELETE':
        return delete_item(id)
    return status(False)


# Runs flask app object 'app'
if __name__ == '__main__':
    app.run(port=config["port"])
