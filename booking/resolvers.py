import os
import grpc
from http import HTTPStatus

import requests
from graphql import GraphQLError
from pymongo.errors import DuplicateKeyError

from auth import AuthError, authorize

import schedule_pb2
import schedule_pb2_grpc
from google.protobuf import wrappers_pb2

USER_SERVICE = os.environ.get("USER_SERVICE", "http://user:3203")
SCHEDULE_SERVICE = os.environ.get("SCHEDULE_SERVICE", "schedule:50052")


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
            channel = grpc.insecure_channel(SCHEDULE_SERVICE)
            stub = schedule_pb2_grpc.ScheduleServiceStub(channel)
            response = stub.GetSchedule(
                wrappers_pb2.StringValue(value=date), timeout=5
            )
            channel.close()
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.NOT_FOUND:
                raise GraphQLError(
                    f"The Schedule for the date {date} doesnt exist",
                    extensions={"code": "INVALID_DATE"},
                )
            raise GraphQLError(
                "Could not load the schedule", extensions={"code": "SERVICE_ERROR"}
            )
        except Exception as error:
            raise GraphQLError(
                "Could not load the schedule", extensions={"code": "SERVICE_ERROR"}
            ) from error

        scheduled_movies = list(response.movies_id)

        for movie in booking_date["movies"]:
            if movie not in scheduled_movies:
                raise GraphQLError(
                    f"The Movie with the id {movie} is not scheduled for this date",
                    extensions={"code": "INVALID_MOVIE"},
                )


def get_all_bookings(_, info):
    """Renvoie toutes les réservations enregistrées en base."""
    return list(info.context["collection"].find({}))


def booking_with_user_id(_, info, _user_id):
    """Recherche la réservation associée à un utilisateur."""
    booking = info.context["collection"].find_one({"userid": _user_id})
    if booking is None:
        raise GraphQLError("Booking for user not found", extensions={"code": "NOT_FOUND"})
    return booking


def create_booking(_, info, _user_id, _dates):
    """Vérifie les données et crée une réservation pour l'utilisateur."""
    verify_user(_user_id)
    if info.context["collection"].find_one({"userid": _user_id}) is not None:
        raise GraphQLError(
            "Booking for this user already exists",
            extensions={"code": "BOOKING_ALREADY_EXISTS"},
        )
    verify_dates(_dates)
    new_booking = {"userid": _user_id, "dates": _dates}
    try:
        info.context["collection"].insert_one(new_booking)
    except DuplicateKeyError as error:
        raise GraphQLError(
            "Booking for this user already exists",
            extensions={"code": "BOOKING_ALREADY_EXISTS"},
        ) from error
    return new_booking


def delete_booking(_, info, _user_id):
    """Supprime la réservation associée à un utilisateur."""
    try:
        current_user = authorize(info.context.get("authorization"))
    except AuthError as error:
        raise GraphQLError(str(error), extensions={"code": error.status.name}) from error
    if current_user["id"] != _user_id:
        raise GraphQLError(
            "You are not authorized to delete this booking",
            extensions={"code": "FORBIDDEN"},
        )
    booking = info.context["collection"].find_one_and_delete({"userid": _user_id})
    if booking is None:
        raise GraphQLError("Booking for user not found", extensions={"code": "NOT_FOUND"})
    return f"Booking for user {_user_id} deleted"
