import json
import os
from concurrent import futures

import grpc
import requests
from http import HTTPStatus

from auth import AuthError, authorize
import schedule_pb2
import schedule_pb2_grpc
from google.protobuf import empty_pb2
from google.protobuf import wrappers_pb2

PORT = 50052
MOVIE_SERVICE = os.environ.get("MOVIE_SERVICE", "http://movie:3200")

with open("{}/databases/times.json".format("."), "r") as jsf:
    schedules = json.load(jsf)["schedule"]


def write(schedules):
    with open("{}/databases/times.json".format("."), "w") as f:
        full = {}
        full["schedule"] = schedules
        json.dump(full, f)


def verify_movies(movies: list[str]):
    try:
        query = """
        query {
            movies {
                id
            }
        }
        """
        response = requests.post(
            f"{MOVIE_SERVICE}/graphql", json={"query": query}, timeout=5
        )

        if response.status_code != HTTPStatus.OK:
            return "SERVICE_ERROR", None

        result = response.json()

        if "errors" in result:
            return "SERVICE_ERROR", None

        movies_in_db = [movie["id"] for movie in result["data"]["movies"]]

    except (requests.RequestException, ValueError, KeyError, TypeError):
        return "SERVICE_ERROR", None

    for movie in movies:
        if movie not in movies_in_db:
            return "INVALID_MOVIE", movie

    return None, None


class ScheduleServiceServicer(schedule_pb2_grpc.ScheduleServiceServicer):

    def GetAllSchedules(self, request, context):
        return schedule_pb2.ScheduleList(
            schedules=[
                schedule_pb2.Schedule(date=s["date"], movies_id=s["movies"])
                for s in schedules
            ]
        )

    def GetSchedule(self, request, context):
        date = request.value
        for s in schedules:
            if str(s["date"]) == str(date):
                return schedule_pb2.Schedule(date=s["date"], movies_id=s["movies"])
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Schedule for date {date} not found")
        return schedule_pb2.Schedule()

    def AddSchedule(self, request, context):
        date = request.date
        movies = list(request.movies_id)

        if any(str(s["date"]) == str(date) for s in schedules):
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"Schedule for date {date} already exists")
            return schedule_pb2.Schedule()

        error_type, value = verify_movies(movies)

        if error_type == "SERVICE_ERROR":
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Could not load the movies")
            return schedule_pb2.Schedule()

        if error_type == "INVALID_MOVIE":
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"The Movie with the id {value} doesnt exist")
            return schedule_pb2.Schedule()

        new_schedule = {"date": date, "movies": movies}
        schedules.append(new_schedule)
        write(schedules)
        return schedule_pb2.Schedule(date=date, movies_id=movies)

    def Delete(self, request, context):
        authorization = dict(context.invocation_metadata()).get("authorization")
        try:
            authorize(authorization, admin=True)
        except AuthError as error:
            codes = {
                HTTPStatus.UNAUTHORIZED: grpc.StatusCode.UNAUTHENTICATED,
                HTTPStatus.FORBIDDEN: grpc.StatusCode.PERMISSION_DENIED,
                HTTPStatus.SERVICE_UNAVAILABLE: grpc.StatusCode.UNAVAILABLE,
            }
            context.abort(codes[error.status], str(error))
        date = request.date
        for s in schedules:
            if str(s["date"]) == str(date):
                schedules.remove(s)
                write(schedules)
                return empty_pb2.Empty()
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Schedule for date {date} not found")
        return empty_pb2.Empty()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    schedule_pb2_grpc.add_ScheduleServiceServicer_to_server(
        ScheduleServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    print(f"Schedule server running on port {PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
