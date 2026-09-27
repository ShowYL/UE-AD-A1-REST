import json
from http import HTTPMethod, HTTPStatus

import requests
from flask import Flask, Response, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found

app = Flask(__name__)

PORT = 3201
HOST = "0.0.0.0"

USER_SERVICE = "http://user:3203"
SCHEDULE_SERVICE = "http://schedule:3202"


with open("./databases/bookings.json", "r") as jsf:
    bookings = json.load(jsf)["bookings"]


def write(bookings):
    with open("./databases/bookings.json", "w") as f:
        json.dump({"bookings": bookings}, f)


def booking_exist(user_id):
    for booking in bookings:
        if str(booking["userid"]) == str(user_id):
            return True
    return False


def get_booking(user_id):
    for booking in bookings:
        if str(booking["userid"]) == str(user_id):
            return booking
    return None


def verify_user(user_id):
    try:
        response = requests.get(f"{USER_SERVICE}/user/{user_id}", timeout=5)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return "INVALID_USER"

        if response.status_code != HTTPStatus.OK:
            return "SERVICE_ERROR"

        response.json()
        return None

    except (requests.RequestException, ValueError):
        return "SERVICE_ERROR"


def get_schedule(date):
    try:
        response = requests.get(f"{SCHEDULE_SERVICE}/schedule/{date}", timeout=5)

        if response.status_code == HTTPStatus.NOT_FOUND:
            return "INVALID_DATE", None

        if response.status_code != HTTPStatus.OK:
            return "SERVICE_ERROR", None

        return None, response.json()

    except (requests.RequestException, ValueError):
        return "SERVICE_ERROR", None


def verify_dates(dates):
    for booking_date in dates:
        date = booking_date["date"]
        requested_movies = booking_date["movies"]

        error, schedule = get_schedule(date)

        if error == "SERVICE_ERROR":
            return "SERVICE_ERROR", None

        if error == "INVALID_DATE":
            return "INVALID_DATE", date

        scheduled_movies = schedule["movies"]  # pyright: ignore[reportOptionalSubscript]

        for movie in requested_movies:
            if movie not in scheduled_movies:
                return "INVALID_MOVIE", movie

    return None, None


@app.route("/", methods=[HTTPMethod.GET])
def home():
    return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route("/bookings", methods=[HTTPMethod.GET])
def get_all_bookings():
    return make_response(bookings, HTTPStatus.OK)


@app.route("/bookings/<user_id>", methods=[HTTPMethod.GET])
@mandatory_url_field(fields=["user_id"])
def get_booking_endpoint(user_id):
    if not booking_exist(user_id):
        return not_found("Booking for user")

    return make_response(get_booking(user_id), HTTPStatus.OK)


@app.route("/bookings", methods=[HTTPMethod.POST])
@mandatory_body_field(fields=["userid", "dates"])
def add_booking():
    data = request.get_json()

    user_id = data["userid"]
    dates = data["dates"]

    user_error = verify_user(user_id)

    if user_error == "SERVICE_ERROR":
        return make_response(
            jsonify({"error": "Could not load the user"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    if user_error == "INVALID_USER":
        return make_response(
            jsonify({"error": f"The User with the id {user_id} doesnt exist"}),
            HTTPStatus.BAD_REQUEST,
        )

    if booking_exist(user_id):
        return make_response(
            jsonify({"error": "Booking for this user already exists"}),
            HTTPStatus.CONFLICT,
        )

    error_type, value = verify_dates(dates)

    if error_type == "SERVICE_ERROR":
        return make_response(
            jsonify({"error": "Could not load the schedule"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    if error_type == "INVALID_DATE":
        return make_response(
            jsonify({"error": f"The Schedule for the date {value} doesnt exist"}),
            HTTPStatus.BAD_REQUEST,
        )

    if error_type == "INVALID_MOVIE":
        return make_response(
            jsonify(
                {
                    "error": f"The Movie with the id {value} is not scheduled for this date"
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    bookings.append(data)
    write(bookings)

    return make_response(data, HTTPStatus.CREATED)


@app.route("/bookings/<user_id>", methods=[HTTPMethod.PUT])
@mandatory_url_field(fields=["user_id"])
@mandatory_body_field(fields=["dates"])
def update_booking(user_id):
    if not booking_exist(user_id):
        return not_found("Booking for user")

    dates = request.get_json()["dates"]

    user_error = verify_user(user_id)

    if user_error == "SERVICE_ERROR":
        return make_response(
            jsonify({"error": "Could not load the user"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    if user_error == "INVALID_USER":
        return make_response(
            jsonify({"error": f"The User with the id {user_id} doesnt exist"}),
            HTTPStatus.BAD_REQUEST,
        )

    error_type, value = verify_dates(dates)

    if error_type == "SERVICE_ERROR":
        return make_response(
            jsonify({"error": "Could not load the schedule"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    if error_type == "INVALID_DATE":
        return make_response(
            jsonify({"error": f"The Schedule for the date {value} doesnt exist"}),
            HTTPStatus.BAD_REQUEST,
        )

    if error_type == "INVALID_MOVIE":
        return make_response(
            jsonify(
                {
                    "error": f"The Movie with the id {value} is not scheduled for this date"
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    booking = get_booking(user_id)
    booking["dates"] = dates  # pyright: ignore[reportOptionalSubscript]

    write(bookings)

    return make_response(booking, HTTPStatus.OK)


@app.route("/bookings/<user_id>", methods=[HTTPMethod.DELETE])
@mandatory_url_field(fields=["user_id"])
def delete_booking(user_id):
    if not booking_exist(user_id):
        return not_found("Booking for user")

    booking = get_booking(user_id)

    bookings.remove(booking)
    write(bookings)

    return Response(status=HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
    print("Server running in port %s" % PORT)
    app.run(host=HOST, port=PORT)
