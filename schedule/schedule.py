import json
from http import HTTPMethod, HTTPStatus
from typing import List

import requests
from flask import Flask, Response, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found

app = Flask(__name__)

PORT = 3202
HOST = "0.0.0.0"

with open("{}/databases/times.json".format("."), "r") as jsf:
    schedules = json.load(jsf)["schedule"]


def write(schedules):
    with open("{}/databases/times.json".format("."), "w") as f:
        full = {}
        full["schedule"] = schedules
        json.dump(full, f)


def verify_movies(movies: List[str]):
    try:
        res = requests.get("http://movie:3200/json", timeout=5)

        if res.status_code != HTTPStatus.OK:
            return "SERVICE_ERROR", None

        response = res.json()
        movies_in_db = [movie["id"] for movie in response]

    except (requests.RequestException, ValueError, KeyError, TypeError):
        return "SERVICE_ERROR", None

    for movie in movies:
        if movie not in movies_in_db:
            return "INVALID_MOVIE", movie

    return None, None


@app.route("/", methods=["GET"])
def home():
    return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"


def schedule_exist(date):
    for schedule in schedules:
        if str(schedule["date"]) == str(date):
            return True
    return False


def get_schedule(date):
    for schedule in schedules:
        if str(schedule["date"]) == str(date):
            return schedule
    return None


@app.route("/schedule", methods=[HTTPMethod.GET])
def get_all_schedule():
    return make_response(schedules, HTTPStatus.OK)


@app.route("/schedule/<date>", methods=[HTTPMethod.GET])
@mandatory_url_field(fields=["date"])
def get_schedule_endpoint(date):
    if not schedule_exist(date):
        return not_found("Schedule for this date")

    return make_response(get_schedule(date), HTTPStatus.OK)


@app.route("/schedule", methods=[HTTPMethod.POST])
@mandatory_body_field(fields=["date", "movies"])
def add_schedule():
    data = request.get_json()

    if schedule_exist(data["date"]):
        return make_response(
            jsonify({"error": "Schedule id exist"}), HTTPStatus.CONFLICT
        )

    error_type, value = verify_movies(data["movies"])

    if error_type == "SERVICE_ERROR":
        return make_response(
            jsonify({"error": "Could not load the movies"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    if error_type == "INVALID_MOVIE":
        return make_response(
            jsonify({"error": f"The Movie with the id {value} doesnt exist"}),
            HTTPStatus.BAD_REQUEST,
        )

    schedules.append(data)
    write(schedules)
    return make_response(data, HTTPStatus.CREATED)


@app.route("/schedule/<date>", methods=[HTTPMethod.DELETE])
@mandatory_url_field(fields=["date"])
def delete_schedule(date):
    if not schedule_exist(date):
        return not_found("Schedule for this date")

    schedule = get_schedule(date)

    schedules.remove(schedule)
    write(schedules)
    return Response(status=HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
