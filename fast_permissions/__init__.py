from typing import Annotated, Callable

from daomodel.db import DAOFactory

from fast_controller import Controller, Action
from fast_controller.util import no_cache
from fastapi import Depends, APIRouter, Response, Request, status, FastAPI, Security, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, APIKeyCookie

from fast_permissions import config
from fast_permissions.exceptions import Unauthorized
from fast_permissions.models import Session, User
from fast_permissions.service import UserService


_security = Security(APIKeyCookie(name='HTTP Only Cookie', description='Must use endpoint to login', auto_error=False))


class Auth:
    """Provides decorators for specifying access levels for endpoints."""
    def access(self, level: str):
        """Decorator that sets the access level of an endpoint i.e. public, restricted, etc..."""
        def wrapper(func):
            func._fp_access = level
            return func
        return wrapper

    @property
    def public(self):
        """Decorator that configures an endpoint to have no access restrictions."""
        return self.access('public')

    @property
    def restricted(self):
        """Decorator that configures an endpoint to require authentication."""
        return self.access('restricted')

auth = Auth()


def default_session_endpoints(router: APIRouter, controller: Controller):
    @router.post('', status_code=status.HTTP_204_NO_CONTENT)
    @auth.public
    async def login(request: Request,
                    response: Response,
                    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                    daos: DAOFactory = controller.daos) -> None:
        """Authenticates the user and sets a cookie with the access token."""
        try:
            user = UserService(daos).authenticate(form_data.username, form_data.password)
            response.set_cookie(
                key='access_token',
                value=user.access_token,
                httponly=True,
                secure=request.url.scheme == 'https',
                samesite='lax',
                max_age=60 * 60 * 24,
                path='/'
            )
        except TypeError:
            if config.SECRET_KEY is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Fast-Permissions SECRET_KEY is not configured')
        except Unauthorized:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username or password')

    @router.delete('', status_code=status.HTTP_204_NO_CONTENT)
    @auth.restricted
    async def logout(response: Response, request: Request, daos: DAOFactory = controller.daos) -> None:
        """Invalidates the caller's token and clears the cookie."""
        caller_token = request.cookies.get('access_token')
        UserService(daos).invalidate_token(caller_token)

        response.status_code = status.HTTP_204_NO_CONTENT
        response.delete_cookie(key='access_token', path='/')

    @no_cache
    @router.head('')
    @auth.restricted
    async def check_auth() -> Response:
        """Checks if the user is authenticated.

        Returns 200 if the caller has a valid access token and 401 otherwise.
        """
        return Response()


class RestrictedRouter(APIRouter):
    """A custom APIRouter that automatically adds authentication middleware.

    :param user_dep: The dependency that validates the user
    :param public_by_default: True to only require authentication for endpoints marked with @auth.restricted
    """
    def __init__(self, *args, user_dep: Depends, public_by_default: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_dep = user_dep
        self.public_by_default = public_by_default

    def add_api_route(self, path, endpoint, **kwargs) -> None:
        """Overrides the default add_api_route method to add authentication middleware."""
        deps = kwargs.pop('dependencies')
        if not deps:
            deps = []

        level = getattr(endpoint, '_fp_access', None)
        if level == 'restricted':
            deps.append(Depends(self.user_dep))
            deps.append(_security)
        elif level == 'public':
            pass
        else:
            if not self.public_by_default:
                deps.append(Depends(self.user_dep))
                deps.append(_security)
        kwargs['dependencies'] = deps
        super().add_api_route(path, endpoint, **kwargs)


class RestrictedController(Controller):
    """A controller that includes authentication middleware."""
    def __init__(self, *args,
                 get_current_user: Callable,
                 public_by_default: bool = False,
                 token_endpoints: Callable = default_session_endpoints,
                 **kwargs):
        self.get_current_user = get_current_user
        self.public_by_default = public_by_default
        super().__init__(*args, **kwargs)
        self.register_resource(Session, skip=set(Action), additional_endpoints=token_endpoints)
        self.register_resource(User)

    def _create_router(self) -> APIRouter:
        return RestrictedRouter(
            prefix=self.prefix,
            user_dep=self.get_current_user,
            public_by_default=self.public_by_default
        )

    def include_controller(self, app: FastAPI) -> None:
        super().include_controller(app)

        @app.exception_handler(Unauthorized)
        async def unauthorized_handler(request: Request, exc: Unauthorized):
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    def register_admin(self, password: str) -> None:
        """Creates an admin user having the given password.

        This only needs to be called once.
        Once logged in as the admin, additional users can be created through the ReST API.

        :param password: The password for the admin user (this will be hashed and stored in the database).
        """
        admin = User(username='admin')
        admin.password = password
        with self.dao_context() as daos:
            daos[User].upsert(admin)
