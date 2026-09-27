import json
from http import HTTPStatus

from flask import Flask, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found

app = Flask(__name__)

PORT = 3203
HOST = "0.0.0.0"

with open("{}/databases/users.json".format("."), "r") as jsf:
    users = json.load(jsf)["users"]


def write(users):
    with open("{}/databases/users.json".format("."), "w") as f:
        full = {}
        full["users"] = users
        json.dump(full, f)


@app.route("/", methods=["GET"])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"


def user_exist(user_id):
    for user in users:
        if str(user_id) == str(user["id"]):
            return True
    return False


def get_user_by_id(user_id):
    for user in users:
        if str(user_id) == str(user["id"]):
            return user
    return None


@app.route("/user/<user_id>", methods=["GET"])
@mandatory_url_field(fields=["user_id"])
def get_user_endpoint(user_id):
    if not user_exist(user_id):
        return not_found("User id")

    return make_response(get_user_by_id(user_id), HTTPStatus.OK)


@app.route("/user/<user_id>", methods=["PUT"])
@mandatory_url_field(fields=["user_id"])
@mandatory_body_field(fields=["name", "last_active"])
def update_user_endpoint(user_id):
    if not user_exist(user_id):
        return not_found("User id")

    user = get_user_by_id(user_id)
    new_user = request.get_json()
    user["name"] = new_user["name"]  # pyright: ignore[reportOptionalSubscript]
    user["last_active"] = new_user["last_active"]  # pyright: ignore[reportOptionalSubscript]
    write(users)
    return make_response(user, HTTPStatus.CREATED)

@app.route("/user", methods=["POST"])
@mandatory_body_field(fields=["id", "name", "last_active"])
def add_user():
    new_user = request.get_json()

    if user_exist(new_user["id"]):
        return make_response(jsonify({"error": "User id exist"}), HTTPStatus.CONFLICT)

    users.append(new_user)
    write(users)
    return make_response(new_user, HTTPStatus.CREATED)

@app.route("/user/<user_id>", methods=["DELETE"])
@mandatory_url_field(fields=["user_id"])
def delete_user(user_id):
    if not user_exist(user_id):
        return not_found("User id")

    user = get_user_by_id(user_id)
    users.remove(user)
    return make_response(user, HTTPStatus.NO_CONTENT)





if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
