import json
from pathlib import Path

from pymongo import MongoClient
from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify, make_response

import resolvers as r

PORT = 3200
HOST = '0.0.0.0'
app = Flask(__name__)


client = MongoClient("mongodb://root:example@mongo:27017/")
db = client["movies"]
existing_collections = db.list_collection_names()

if "movies" not in existing_collections:
    with (Path(__file__).parent / "databases" / "movies.json").open() as file:
        db["movies"].insert_many(json.load(file)["movies"])

if "actors" not in existing_collections:
    with (Path(__file__).parent / "databases" / "actors.json").open() as file:
        db["actors"].insert_many(json.load(file)["actors"])

db["movies"].create_index("id", unique=True)
db["actors"].create_index("id", unique=True)

# Chargement des types déclarés dans movie.graphql
type_defs = load_schema_from_path('movie.graphql')

# Création des objets associés au schéma
query = QueryType()
mutation = MutationType()
movie = ObjectType('Movie')
actor = ObjectType('Actor')

# Association des resolvers écrits avec ceux des schémas
query.set_field('movie_with_id', r.movie_with_id)
query.set_field('movies', r.get_all_movies)
query.set_field('movie_by_title', r.movie_by_title)
query.set_field('movies_by_minrate', r.movies_by_minrate)
mutation.set_field('update_movie_rate', r.update_movie_rate)
mutation.set_field('update_movie', r.update_movie)
mutation.set_field('create_movie', r.create_movie)
mutation.set_field('delete_movie', r.delete_movie)
movie.set_field('actors', r.resolve_actors_in_movie)

# Création du schéma exécutable
schema = make_executable_schema(type_defs, movie, query, mutation, actor)

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>",200)

# graphql entry points
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
                        schema,
                        data,
                        context_value={"collection": db["movies"], "actors": db["actors"]},
                        debug=app.debug
                    )
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)
