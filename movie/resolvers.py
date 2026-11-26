from graphql import GraphQLError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth import AuthError, authorize

def get_all_movies(_, info):
    """Renvoie tous les films enregistrés en base."""
    return list(info.context["collection"].find({}))

def movie_with_id(_, info, _id):
    """Recherche un film par son identifiant, ou renvoie None."""
    return info.context["collection"].find_one({"id": _id})

def movie_by_title(_, info, _title):
    """Recherche un film par son titre exact, ou renvoie None."""
    return info.context["collection"].find_one({"title": _title})

def movies_by_minrate(_, info, _rating):
    """Renvoie les films dont la note est strictement supérieure à _rating."""
    return list(info.context["collection"].find({"rating": {"$gt": _rating}}))

def update_movie_rate(_, info, _id, _rate):
    """Met à jour la note d'un film et renvoie le film modifié."""
    return update_movie(_, info, _id, _rating=_rate)

def update_movie(_, info, _id, _title=None, _rating=None, _director=None):
    """Met à jour les champs fournis et renvoie le film modifié."""
    updates = {
        "title": _title,
        "rating": _rating,
        "director": _director,
    }
    updates = {field: value for field, value in updates.items() if value is not None}

    if not updates:
        raise GraphQLError("Fournissez au moins un champ à modifier")

    movie = info.context["collection"].find_one_and_update(
        {"id": _id}, {"$set": updates}, return_document=ReturnDocument.AFTER
    )
    if movie is None:
        raise GraphQLError("Aucun film trouvé avec cet identifiant")
    return movie

def resolve_actors_in_movie(movie, info):
    """Renvoie les acteurs associés à ce film."""
    return list(info.context["actors"].find({"films": movie["id"]}))

def create_movie(_, info, _id, _title, _rating, _director):
    """Crée un film et signale une erreur si son identifiant existe déjà."""
    movie = {
        "id": _id,
        "title": _title,
        "rating": _rating,
        "director": _director,
    }
    try:
        info.context["collection"].insert_one(movie)
    except DuplicateKeyError as error:
        raise GraphQLError("Un film avec cet identifiant existe déjà") from error
    return movie

def delete_movie(_, info, _id):
    """Supprime un film par son identifiant et confirme sa suppression."""
    try:
        authorize(info.context.get("authorization"), admin=True)
    except AuthError as error:
        raise GraphQLError(str(error), extensions={"code": error.status.name}) from error
    movie = info.context["collection"].find_one_and_delete({"id": _id})
    if movie is None:
        raise GraphQLError("Aucun film trouvé avec cet identifiant")
    return f"Film « {movie['title']} » supprimé"
