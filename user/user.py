import json
from http import HTTPMethod, HTTPStatus
from time import time

from flask import Flask, Response, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

app = Flask(__name__)

PORT = 3203
HOST = "0.0.0.0"

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)

with open("{}/databases/users.json".format("."), "r") as jsf:
    users = json.load(jsf)["users"]

def write(users):
    with open("{}/databases/users.json".format("."), "w") as f:
        full = {}
        full["users"] = users
        json.dump(full, f)


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


@app.route("/", methods=[HTTPMethod.GET])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"

@app.route("/json", methods=[HTTPMethod.GET])
def json_users():
    return make_response(jsonify({"users": users}), HTTPStatus.OK)

@app.route("/login", methods=["POST"])
@mandatory_body_field(fields=["name", "password"])
def login():
    data = request.get_json()
    userId = data.get("name").lower().replace(" ", "_")
    password = data.get("password")

    for user in users:
        if user["id"] == userId and user["password"] == password:
            access_token = create_access_token(identity=userId)
            return make_response(jsonify({"access_token": access_token}), HTTPStatus.OK)

    return make_response(jsonify({"error": "Invalid credentials"}), HTTPStatus.UNAUTHORIZED)


@app.route("/auth/verify", methods=[HTTPMethod.GET])
@jwt_required()
def verify_auth():
    user = get_user_by_id(get_jwt_identity())
    if user is None:
        return make_response(jsonify({"error": "User no longer exists"}), HTTPStatus.UNAUTHORIZED)
    return jsonify({"id": user["id"], "role": user.get("role", "user")})


@app.route("/user/<user_id>", methods=[HTTPMethod.GET])
@mandatory_url_field(fields=["user_id"])
def get_user_endpoint(user_id):
    if not user_exist(user_id):
        return not_found("User id")

    return make_response(get_user_by_id(user_id), HTTPStatus.OK)


@app.route("/user/<user_id>", methods=[HTTPMethod.PUT])
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


@app.route("/register", methods=[HTTPMethod.POST])
@mandatory_body_field(fields=["name", "password"])
def add_user():
    new_user = request.get_json()

    user_id = new_user["name"].lower().replace(" ", "_")
    if user_exist(user_id):
        return make_response(jsonify({"error": "User name already exists"}), HTTPStatus.CONFLICT)

    new_user["id"] = user_id
    new_user["role"] = "user"
    new_user.setdefault("last_active", int(time()))
    users.append(new_user)
    write(users)
    response_user = new_user.copy()
    response_user.pop("password", None)
    return make_response(response_user, HTTPStatus.CREATED)


@app.route("/user/<user_id>", methods=[HTTPMethod.DELETE])
@jwt_required()
@mandatory_url_field(fields=["user_id"])
def delete_user(user_id):
    current_user = get_user_by_id(get_jwt_identity())
    if current_user is None:
        return make_response(jsonify({"error": "User no longer exists"}), HTTPStatus.UNAUTHORIZED)

    if current_user["id"] != user_id and current_user.get("role") != "admin":
        return make_response(jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN)

    if not user_exist(user_id):
        return not_found("User id")

    user = get_user_by_id(user_id)
    users.remove(user)
    write(users)
    return Response(status=HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
