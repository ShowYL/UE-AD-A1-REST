from functools import wraps
from http import HTTPStatus

from flask import jsonify, make_response, request


def mandatory_url_field(fields: list[str]):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for field in fields:
                path_value = request.view_args.get(field) if request.view_args else None
                query_value = request.args.get(field)

                if path_value is None and query_value is None:
                    return make_response(
                        jsonify({"error": f"No data provided for the field {field}"}),
                        HTTPStatus.BAD_REQUEST,
                    )
            return func(*args, **kwargs)

        return wrapper

    return inner


def mandatory_body_field(fields: list[str]):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return make_response(
                    jsonify({"error": "A body must be provided"}),
                    HTTPStatus.BAD_REQUEST,
                )

            for field in fields:
                if field not in data or data[field] is None:
                    return make_response(
                        jsonify({"error": f"No data provided for the field {field}"}),
                        HTTPStatus.BAD_REQUEST,
                    )
            return func(*args, **kwargs)

        return wrapper

    return inner


def not_found(value):
    return make_response(jsonify({"error": f"{value} not found"}), HTTPStatus.NOT_FOUND)
