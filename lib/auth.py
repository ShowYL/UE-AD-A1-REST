import os
from http import HTTPStatus

import requests


USER_SERVICE = "http://user:3203"


class AuthError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def authorize(authorization, admin=False):
    # Verify that the authorization header is present
    if not authorization:
        raise AuthError(HTTPStatus.UNAUTHORIZED, "Authentication required")

    try:
        response = requests.get(
            f"{USER_SERVICE}/auth/verify",
            headers={"Authorization": authorization},
            timeout=5,
        )
    except requests.RequestException as error:
        raise AuthError(HTTPStatus.SERVICE_UNAVAILABLE, "User service unavailable") from error

    # Check if the response indicates an invalid or expired token
    if response.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.UNPROCESSABLE_ENTITY):
        raise AuthError(HTTPStatus.UNAUTHORIZED, "Invalid or expired token")
    if response.status_code != HTTPStatus.OK:
        raise AuthError(HTTPStatus.SERVICE_UNAVAILABLE, "User service unavailable")

    # Parse the user information from the response
    try:
        user = response.json()
        role = user["role"]
    except (ValueError, KeyError, TypeError) as error:
        raise AuthError(HTTPStatus.SERVICE_UNAVAILABLE, "Invalid user service response") from error

    # Check if the user has the required role if admin access is needed
    if admin and role != "admin":
        raise AuthError(HTTPStatus.FORBIDDEN, "Admin role required")
