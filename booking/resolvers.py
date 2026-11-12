import json
import os
from http import HTTPStatus
from pathlib import Path

import requests
from graphql import GraphQLError

BOOKINGS_FILE = Path(__file__).parent / "databases" / "bookings.json"
USER_SERVICE = os.environ.get("USER_SERVICE", "http://user:3203")
SCHEDULE_SERVICE = os.environ.get("SCHEDULE_SERVICE", "http://schedule:3202")


def load_bookings():
    with open(BOOKINGS_FILE, "r") as file:
        return json.load(file)


def write_bookings(data):
    with open(BOOKINGS_FILE, "w") as file:
        json.dump(data, file, indent=2)


def verify_user(user_id):
    try:
        response = requests.get(f"{USER_SERVICE}/user/{user_id}", timeout=5)
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise GraphQLError(
                f"The User with the id {user_id} doesnt exist",
                extensions={"code": "INVALID_USER"},
            )
        if response.status_code != HTTPStatus.OK:
            raise GraphQLError("Could not load the user", extensions={"code": "SERVICE_ERROR"})
        response.json()
    except (requests.RequestException, ValueError) as error:
        raise GraphQLError(
            "Could not load the user", extensions={"code": "SERVICE_ERROR"}
        ) from error


def verify_dates(dates):
    for booking_date in dates:
        date = booking_date["date"]
        try:
            response = requests.get(f"{SCHEDULE_SERVICE}/schedule/{date}", timeout=5)
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise GraphQLError(
                    f"The Schedule for the date {date} doesnt exist",
                    extensions={"code": "INVALID_DATE"},
                )
            if response.status_code != HTTPStatus.OK:
                raise GraphQLError(
                    "Could not load the schedule", extensions={"code": "SERVICE_ERROR"}
                )
            schedule = response.json()
            scheduled_movies = schedule["movies"]
            if not isinstance(scheduled_movies, list):
                raise ValueError("Invalid schedule movies")
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            raise GraphQLError(
                "Could not load the schedule", extensions={"code": "SERVICE_ERROR"}
            ) from error

        for movie in booking_date["movies"]:
            if movie not in scheduled_movies:
                raise GraphQLError(
                    f"The Movie with the id {movie} is not scheduled for this date",
                    extensions={"code": "INVALID_MOVIE"},
                )


def get_all_bookings(_, info):
    return load_bookings()["bookings"]


def booking_with_user_id(_, info, _user_id):
    for booking in load_bookings()["bookings"]:
        if str(booking["userid"]) == _user_id:
            return booking
    raise GraphQLError("Booking for user not found", extensions={"code": "NOT_FOUND"})


def create_booking(_, info, _user_id, _dates):
    verify_user(_user_id)
    data = load_bookings()

    for booking in data["bookings"]:
        if str(booking["userid"]) == _user_id:
            raise GraphQLError(
                "Booking for this user already exists",
                extensions={"code": "BOOKING_ALREADY_EXISTS"},
            )

    verify_dates(_dates)
    new_booking = {"userid": _user_id, "dates": _dates}
    data["bookings"].append(new_booking)
    write_bookings(data)
    return new_booking


def delete_booking(_, info, _user_id):
    data = load_bookings()
    for booking in data["bookings"]:
        if str(booking["userid"]) == _user_id:
            data["bookings"].remove(booking)
            write_bookings(data)
            return f"Booking for user {_user_id} deleted"
    raise GraphQLError("Booking for user not found", extensions={"code": "NOT_FOUND"})
