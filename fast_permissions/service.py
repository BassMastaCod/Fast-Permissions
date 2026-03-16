from datetime import timedelta, datetime, timezone
from typing import Optional, Any

import jwt
from daomodel.dao import NotFound
from daomodel.db import DAOFactory
from fastapi import HTTPException

from fast_permissions import config
from fast_permissions.exceptions import InvalidPassword, Unauthorized
from fast_permissions.models import User, Session, OwnedResource


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token.

    :param data: The payload to include in the token
    :param expires_delta: The duration for which the token is valid
    :return: The encoded access token
    """
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode = {**data, 'exp': expire}
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decodes a JWT token and returns the payload."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        if not payload.get('username'):
            raise HTTPException(status_code=401, detail='Invalid token')
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')


class UserService:
    def __init__(self, daos: DAOFactory):
        self.daos = daos
        self.user_dao = daos[User]
        self.token_dao = daos[Session]

    def register(self, username: str, password: str) -> User:
        """Creates a new User and saves it to the database.

        :param username: The new username
        :param password: The unencrypted password for the new username
        :return: The newly created User
        :raises PrimaryKeyConflict: If the username is already taken
        """
        user = self.user_dao.create_with(commit=False, username=username)
        self.set_password(user, password)
        return user

    def authenticate(self, username: str, password: str) -> User:
        """Authenticates a User and returns a token if successful.

        :param username: The username to authenticate
        :param password: The unencrypted password for the username
        :return: The authenticated User, containing the access token
        :raises HTTPException: If the username or password is incorrect
        """
        try:
            user = self.get_user(username)
            user.verify(password)
            user.access_token = create_access_token(user.model_dump(), expires_delta=timedelta(days=1))
            self.token_dao.create_with(access_token=user.access_token, owner=user.username)
            return user
        except (NotFound, InvalidPassword) as e:
            raise Unauthorized('Authentication failed due to incorrect username or password') from e

    def get_user(self, username: str) -> User:
        """Finds a User by their username."""
        return self.user_dao.get(username)

    def set_password(self, user: User, password: str) -> None:
        """Sets a new password for a user and updates the User record in the database."""
        user.password = password
        self.user_dao.update(user)

    def get_owned(self, user: User, resource: type[OwnedResource]) -> list[OwnedResource]:
        """Returns resources that belong to a specific User.

        :param user: The user whose resources to find
        :param resource: The type of resource to find
        :return: A list of resources owned by the user
        """
        return self.daos[resource].find(owner=user.username)

    def from_token(self, token: str) -> User:
        """Finds a User by their token.

        :param token: The token the User is authenticated with
        :return: The User associated with the token
        """
        if not token:
            raise Unauthorized('No token provided')
        try:
            payload = decode_token(token)
            username = payload['username']
            self.token_dao.get(token)
            return self.get_user(username)
        except Exception as e:
            raise Unauthorized(f'Authentication failed: {str(e)}') from e

    def invalidate_token(self, token: str) -> None:
        """Deauthenticates a session by invalidating its token."""
        if not token:
            return
        try:
            entry = self.token_dao.get(token)
            self.token_dao.remove(entry)
        except NotFound:
            pass
