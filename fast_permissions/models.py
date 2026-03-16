from typing import Optional, Any

import bcrypt
from daomodel.fields import Identifier, Unsearchable
from fast_controller import Resource
from fast_controller.schema import schemas

from fast_permissions.exceptions import InvalidPassword


class UserBase(Resource):
    username: Identifier[str]


@schemas(output=UserBase)
class User(UserBase, table=True):
    password: Unsearchable[str]

    def __setattr__(self, key: str, value: Any) -> None:
        # Automatically hash any set password
        if key == 'password':
            value = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        super.__setattr__(self, key, value)

    def verify(self, password: str) -> None:
        """Verify the user's password, raises InvalidPassword if incorrect."""
        if not bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8')):
            raise InvalidPassword()


class OrphanableResource(Resource):
    """A resource that can be owned by a user, but not necessarily."""
    __abstract__ = True
    owner: Optional[User]

    def is_owned(self) -> bool:
        return self.owner is not None

    def is_owned_by(self, user: User) -> bool:
        return self.owner == user.username


class OwnedResource(OrphanableResource):
    """A resource that belongs to a specific User."""
    __abstract__ = True
    owner: User


class Session(OwnedResource, table=True):
    access_token: Identifier[str]
    token_type: str = 'bearer'  # is this valid or needed/weanted?
