from pathlib import Path
from typing import Optional, Callable
from urllib.parse import quote

from daomodel.db import init_db, create_engine
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from fast_permissions import RestrictedController
from fast_permissions.html import login_template
from fast_permissions.models import User
from fast_permissions.service import Unauthorized, UserService

try:
    from fastpwa import PWA, ensure_list, logger
except ImportError:
    raise ImportError(
        'PWAWithAuth requires FastPWA. Install with: pip install fast-permissions[pwa]'
    )


class Redirect(HTTPException):
    """HTTP Response that redirects the client to the given URL."""
    def __init__(self, url: str, code: int = status.HTTP_302_FOUND):
        super().__init__(
            status_code=code,
            headers={"Location": url}
        )


class PWAWithAuth(PWA):
    """Extension of PWA that adds authentication functionality.

    This implementation provides a way to create pages that require authentication.
    """
    def __init__(self, *args,
                 get_current_user: Optional[Callable] = None,
                 public_by_default: Optional[bool] = None,
                 unauthorized_redirect: Optional[str] = None,
                 **kwargs):
        self.get_current_user = get_current_user or self._default_get_current_user
        self.public_by_default = public_by_default
        if public_by_default is not None:
            if get_current_user:
                raise ValueError('`public_by_default` can only be set if not using a custom `get_current_user` function')
        self.unauthorized_redirect = unauthorized_redirect
        super().__init__(*args, **kwargs)

    def _default_controller(self):
        controller = RestrictedController(
            prefix=self.api_prefix,
            get_current_user=self.get_current_user,
            public_by_default=self.public_by_default
        )
        controller.engine = create_engine('database.db')
        init_db(controller.engine)
        return controller

    def _default_get_current_user(self, request: Request) -> User:
        """Returns the currently logged-in user, or raises Unauthorized if not logged in."""
        token = request.cookies.get('access_token')
        with self.controller.dao_context() as daos:
            return UserService(daos).from_token(token)

    @property
    def restricted_dep(self):
        return Depends(self.get_current_user_with_redirect(no_return=True))

    def register_simple_login_page(self,
            page_path: str = 'login',
            api_path: str = '/api/sessions',
            redirect: bool = True) -> None:
        """Creates a basic login page.

        This page is extremely rudimentary and is only intended for developer use.
        UX is lacking; it does not redirect after login or even provide feedback to the user.

        :param page_path: Where to host the login page (/login by default)
        :param api_path: Where to send the login form (/api/sessions by default)
        :param redirect: False to avoid automatically redirecting to this page when not logged in
        """
        @self.page(page_path, html=login_template.replace('${path}', api_path))
        async def login_page() -> dict:
            return {'title': f'{self.title} Login'}

        if redirect:
            self.unauthorized_redirect = '/login'

    def get_current_user_with_redirect(self, url: Optional[str] = None, no_return: bool = False):
        """Returns a dependency that validates the user and redirects back to the original page once logged in."""
        if not url:
            if not self.unauthorized_redirect:
                raise ValueError('Unauthorized redirect URL not specified. '
                                 'Please set unauthorized_redirect= when creating PWA or page.')
            url = self.unauthorized_redirect
        async def wrapper(request: Request):
            try:
                return self.get_current_user(request)
            except Unauthorized:
                if no_return:
                    raise Redirect(url)
                original = quote(request.url.path)
                sep = '&' if '?' in url else '?'
                raise Redirect(f'{url}{sep}from={original}')
        return wrapper

    def restricted_page(self,
                        route: str,
                        html: str | Path,
                        css: Optional[str | list[str]] = None,
                        js: Optional[str | list[str]] = None,
                        js_libraries: Optional[str | list[str]] = None,
                        color: Optional[str] = None,
                        unauthorized_redirect: Optional[str] = None,
                        **get_kwargs):
        """Decorator that creates a page requiring authentication."""
        route = self.with_prefix(route)
        url = unauthorized_redirect or self.unauthorized_redirect
        get_user = self.get_current_user_with_redirect(url) if url else self.get_current_user

        def decorator(func):
            async def response_wrapper(request: Request, context: dict = Depends(func), user: User = Depends(get_user)):
                return HTMLResponse(self.page_template.render(
                    path_prefix=self.prefix,
                    request=request,
                    title=context.get('title', self.title),
                    color=color,
                    css=ensure_list(css) + self.global_css,
                    js=ensure_list(js) + self.global_js,
                    js_libraries=ensure_list(js_libraries),
                    body=self.env.get_template(html).render(**context)
                ))
            self.get(route, include_in_schema=False, **get_kwargs)(response_wrapper)
            logger.info(f'Registered restricted page at {route}')
            return func
        return decorator
