import json
import sys

from flask import Flask, jsonify, make_response, request
from utils import mandatory_body_field, mandatory_url_field, not_found
from werkzeug.exceptions import NotFound

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
    old_movie["rating"] = int(new_movie["rating"])
    old_movie["director"] = new_movie["director"]


# root message
@app.route("/", methods=["GET"])
def home():
    return make_response(
        "<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200
    )


@app.route("/json", methods=["GET"])
def getAll():
    return make_response(jsonify(movies), 200)


@app.route("/movies/<movieId>", methods=["GET"])
@mandatory_url_field(fields=["movieId"])
def get_movie_by_id_endpoint(movieId):
    if not movie_exist(movieId):
        return not_found("Movie id")

    movie = get_movie_by_id(movieId)
    return make_response(movie, 200)


@app.route("/movies/<movieId>/<rate>", methods=["PATCH"])
@mandatory_url_field(fields=["movieId", "rate"])
def update_movie_rating(movieId, rate):
    if not movie_exist(movieId):
        return not_found("Movie id")

    movie = get_movie_by_id(movieId)
    movie["rating"] = int(rate)  # pyright: ignore[reportOptionalSubscript]
    write(movies)

    return make_response(movie, 200)


@app.route("/movies/<movieId>", methods=["PUT"])
@mandatory_url_field(fields=["movieId"])
@mandatory_body_field(fields=["title", "rating", "director"])
def update_movie_endpoint(movieId):
    if not movie_exist(movieId):
        return not_found("Movie id")

    movie = get_movie_by_id(movieId)
    new_movie = request.get_json()
    update_movie(movie, new_movie)

    write(movies)
    return make_response(movie, 200)


@app.route("/movies", methods=["POST"])
@mandatory_body_field(fields=["id", "title", "rating", "director"])
def add_movie():
    movie = request.get_json()

    if movie_exist(movie["id"]):
        return make_response(jsonify({"error": "Movie id exist"}), 409)

    movies.append(movie)
    write(movies)
    return make_response(movie, 200)


@app.route("/movies/title", methods=["GET"])
@mandatory_url_field(fields=["title"])
def get_movie_by_title():
    title = request.args["title"]
    for movie in movies:
        if str(movie["title"]) == str(title):
            return make_response(movie, 200)

    return not_found("Movie title")


@app.route("/movies/<movieId>", methods=["DELETE"])
@mandatory_url_field(fields=["movieId"])
def delete_movie(movieId):
    if not movie_exist(movieId):
        return not_found("Movie id")

    movie = get_movie_by_id(movieId)

    movies.remove(movie)
    write(movies)
    return make_response(None, 204)


if __name__ == "__main__":
    # p = sys.argv[1]
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
