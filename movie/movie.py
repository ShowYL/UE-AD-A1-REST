import json
from http import HTTPMethod, HTTPStatus

from flask import Flask, Response, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found

app = Flask(__name__)

PORT = 3200
HOST = "0.0.0.0"

with open("{}/databases/movies.json".format("."), "r") as jsf:
    movies = json.load(jsf)["movies"]


def write(movies):
    with open("{}/databases/movies.json".format("."), "w") as f:
        full = {}
        full["movies"] = movies
        json.dump(full, f)


def movie_exist(id):
    for movie in movies:
        if str(movie["id"]) == str(id):
            return True
    return False


def get_movie_by_id(id):
    for movie in movies:
        if str(movie["id"]) == str(id):
            return movie
    return None


def update_movie(old_movie, new_movie):
    old_movie["title"] = new_movie["title"]
    old_movie["rating"] = float(new_movie["rating"])
    old_movie["director"] = new_movie["director"]


# root message
@app.route("/", methods=[HTTPMethod.GET])
def home():
    return make_response(
        "<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200
    )


@app.route("/json", methods=[HTTPMethod.GET])
def getAll():
    return make_response(jsonify(movies), HTTPStatus.OK)


@app.route("/movies/<movie_id>", methods=[HTTPMethod.GET])
@mandatory_url_field(fields=["movie_id"])
def get_movie_by_id_endpoint(movie_id):
    if not movie_exist(movie_id):
        return not_found("Movie id")

    movie = get_movie_by_id(movie_id)
    return make_response(movie, HTTPStatus.OK)


@app.route("/movies/<movie_id>/<rate>", methods=[HTTPMethod.PATCH])
@mandatory_url_field(fields=["movie_id", "rate"])
def update_movie_rating(movie_id, rate):
    if not movie_exist(movie_id):
        return not_found("Movie id")

    movie = get_movie_by_id(movie_id)
    movie["rating"] = float(rate)  # pyright: ignore[reportOptionalSubscript]
    write(movies)

    return make_response(movie, HTTPStatus.OK)


@app.route("/movies/<movie_id>", methods=[HTTPMethod.PUT])
@mandatory_url_field(fields=["movie_id"])
@mandatory_body_field(fields=["title", "rating", "director"])
def update_movie_endpoint(movie_id):
    if not movie_exist(movie_id):
        return not_found("Movie id")

    movie = get_movie_by_id(movie_id)
    new_movie = request.get_json()
    update_movie(movie, new_movie)

    write(movies)
    return make_response(movie, HTTPStatus.OK)


@app.route("/movies", methods=[HTTPMethod.POST])
@mandatory_body_field(fields=["id", "title", "rating", "director"])
def add_movie():
    movie = request.get_json()

    if movie_exist(movie["id"]):
        return make_response(jsonify({"error": "Movie id exist"}), HTTPStatus.CONFLICT)

    movies.append(movie)
    write(movies)
    return make_response(movie, HTTPStatus.CREATED)


@app.route("/movies", methods=[HTTPMethod.GET])
@mandatory_url_field(fields=["title"])
def get_movie_by_title():
    title = request.args["title"]
    for movie in movies:
        if str(movie["title"]) == str(title):
            return make_response(movie, HTTPStatus.OK)

    return not_found("Movie title")


@app.route("/movies/<movie_id>", methods=[HTTPMethod.DELETE])
@mandatory_url_field(fields=["movie_id"])
def delete_movie(movie_id):
    if not movie_exist(movie_id):
        return not_found("Movie id")

    movie = get_movie_by_id(movie_id)

    movies.remove(movie)
    write(movies)
    return Response(status=HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
    # p = sys.argv[1]
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
