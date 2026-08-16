import uuid

from daomodel.dao import NotFound
from daomodel.db import DAOFactory

from fast_permissions.exceptions import InvalidPassword, Unauthorized
from fast_permissions.models import User, Session, OwnedResource


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

    def authenticate(self, username: str, password: str) -> tuple[User, str]:
        """Authenticates a User and returns a token if successful.

        :param username: The username to authenticate
        :param password: The unencrypted password for the username
        :return: The authenticated User, containing the access token
        :raises HTTPException: If the username or password is incorrect
        """
        try:
            user = self.get_user(username)
            user.verify(password)
            token = self.token_dao.create_with(access_token=uuid.uuid4().hex, owner=user.username)
            return user, token.access_token
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
            entry = self.token_dao.get(token)
            return self.get_user(entry.owner)
        except NotFound as e:
            raise Unauthorized('Invalid token') from e

    def invalidate_token(self, token: str) -> None:
        """Deauthenticates a session by invalidating its token."""
        if not token:
            return
        try:
            entry = self.token_dao.get(token)
            self.token_dao.remove(entry)
        except NotFound:
            pass
