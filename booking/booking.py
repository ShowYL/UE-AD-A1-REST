import json
from pathlib import Path

from ariadne import MutationType, QueryType, graphql_sync, load_schema_from_path, make_executable_schema
from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient

import resolvers as r

PORT = 3201
HOST = "0.0.0.0"
app = Flask(__name__)

client = MongoClient("mongodb://root:example@mongo:27017/")
db = client["booking"]

if "bookings" not in db.list_collection_names():
    with (Path(__file__).parent / "databases" / "bookings.json").open() as file:
        db["bookings"].insert_many(json.load(file)["bookings"])

db["bookings"].create_index("userid", unique=True)

type_defs = load_schema_from_path('booking.graphql')

query = QueryType()
mutation = MutationType()

query.set_field("bookings", r.get_all_bookings)
query.set_field("booking_with_user_id", r.booking_with_user_id)
mutation.set_field("create_booking", r.create_booking)
mutation.set_field("delete_booking", r.delete_booking)

schema = make_executable_schema(type_defs, query, mutation)


@app.route("/", methods=["GET"])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Booking service!</h1>", 200)


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema, data, context_value={"collection": db["bookings"],
                                     "authorization": request.headers.get("Authorization")}, debug=app.debug
    )
    return jsonify(result), 200 if success else 400


if __name__ == "__main__":
    print("Server running in port %s" % PORT)
    app.run(host=HOST, port=PORT)
