import json
from graphql import GraphQLError

def movie_with_id(_, info, _id):
    with open('{}/databases/movies.json'.format("."), "r") as file:
        movies = json.load(file)
        for movie in movies['movies']:
            if movie['id'] == _id:
                return movie

def update_movie_rate(_, info, _id, _rate):
    newMovies = {}
    newMovie = {}

    with open('{}/databases/movies.json'.format("."), "r") as rfile:
        movies = json.load(rfile)
        for movie in movies["movies"]:
            if movie["id"] == _id:
                movie["rating"] = _rate
                newMovie = movie
                newMovies = movies

    with open('{}/databases/movies.json'.format("."), "w") as wfile:
        json.dump(newMovies, wfile)

    return newMovie

def update_movie(_, info, _id, _title=None, _rating=None, _director=None):
    updates = {
        "title": _title,
        "rating": _rating,
        "director": _director,
    }
    updates = {field: value for field, value in updates.items() if value is not None}

    if not updates:
        raise GraphQLError("Fournissez au moins un champ à modifier")

    with open("./databases/movies.json", "r") as file:
        data = json.load(file)

    movie = None
    for candidate in data["movies"]:
        if candidate["id"] == _id:
            movie = candidate
            break

    if movie is None:
        raise GraphQLError("Aucun film trouvé avec cet identifiant")

    movie.update(updates)

    with open("./databases/movies.json", "w") as file:
        json.dump(data, file, indent=2)

    return movie

def resolve_actors_in_movie(movie, info):
    with open('{}/databases/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
        return result

def create_movie(_, info, _id, _title, _rating, _director):
    with open('{}/databases/movies.json'.format("."), "r") as rfile:
        movies = json.load(rfile)
    
    for movie in movies["movies"]:
        if movie["id"] == _id:
            raise GraphQLError("Un film avec cet identifiant existe déjà")

    newMovie = {
        "id": _id,
        "title": _title,
        "rating": _rating,
        "director": _director
    }

    movies["movies"].append(newMovie)

    with open('{}/databases/movies.json'.format("."), "w") as wfile:
        json.dump(movies, wfile)

    return newMovie

def delete_movie(_, info, _id):
    with open('{}/databases/movies.json'.format("."), "r") as rfile:
            movies = json.load(rfile)

    remaining_movies = []
    deleted_movie = None

    for movie in movies["movies"]:
        if movie["id"] == _id:
            deleted_movie = movie
        else:
            remaining_movies.append(movie)

    if deleted_movie is None:
        raise GraphQLError("Aucun film trouvé avec cet identifiant")

    movies["movies"] = remaining_movies

    with open('{}/databases/movies.json'.format("."), "w") as wfile:
        json.dump(movies, wfile)

    return f"Film « {movie['title']} » supprimé"