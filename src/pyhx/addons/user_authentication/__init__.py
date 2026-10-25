"""Cookie-backed user authentication for PyHX apps.

Wire it on a :class:`WebApp` with :func:`configure_user_authentication`,
which handles three things in one call:

1. The session middleware (:class:`CookieUserSession` +
   Starlette's ``SessionMiddleware``) that turns the signed
   ``pyhx_session`` cookie into a populated
   :attr:`pyhx.core.RequestContext.user` on every HTTP / WebSocket
   scope.
2. Default ``/login`` and ``/logout`` pages. The login page offers the
   configured ``login_methods``: username and password
   (:class:`PasswordLogin`, the default) and/or a link and code sent by
   email (:class:`EmailTokenLogin`).
3. A FastAPI exception handler that converts :class:`NotAuthenticated`
   — raised by callers like :func:`require_authenticated_user` — into
   a redirect to the login page, preserving the originating URL via
   ``?next=``.

Any of the three can be turned off via the corresponding
``include_…`` flags on :func:`configure_user_authentication`.
"""

from collections.abc import Sequence
from typing import Any, Literal

from commons.users import UsersRepository

from pyhx.core import PageTemplate, WebApp
from pyhx.core.primitives import Omit, omit

from ._accessors import (
    require_authenticated_user,
    require_registered_user,
    require_user,
)
from ._exception import NotAuthenticated, make_not_authenticated_handler
from ._methods import EmailTokenLogin, LoginMethod, PasswordLogin
from ._pages import default_login_page_template, register_default_auth_pages
from ._session import (
    SESSION_USER_ID_KEY,
    CookieUserSession,
    UserSessionSettings,
    configure_user_session,
    login_user,
    logout_user,
)

__all__ = [
    "SESSION_USER_ID_KEY",
    "CookieUserSession",
    "EmailTokenLogin",
    "LoginMethod",
    "NotAuthenticated",
    "PasswordLogin",
    "UserSessionSettings",
    "configure_user_authentication",
    "configure_user_session",
    "login_user",
    "logout_user",
    "require_authenticated_user",
    "require_registered_user",
    "require_user",
]


def configure_user_authentication(
    webapp: WebApp,
    *,
    users: UsersRepository,
    login_methods: Sequence[LoginMethod] | None = None,
    default_login_method: type[LoginMethod] | None | Omit = omit,
    login_page_template: PageTemplate | None = None,
    secret_key: str | None = None,
    session_cookie: str | None = None,
    max_age: int | None = None,
    same_site: Literal["lax", "strict", "none"] | None = None,
    https_only: bool | None = None,
    domain: str | None = None,
    path: str | None = None,
    include_default_pages: bool = True,
    include_exception_handler: bool = True,
    login_path: str = "/login",
    logout_path: str = "/logout",
    post_login_redirect: str = "/",
    post_logout_redirect: str = "/login",
    **session_extras: Any,
) -> None:
    """Wire the session middleware, the built-in ``/login`` / ``/logout``
    pages, and the :class:`NotAuthenticated` exception handler on
    ``webapp``.

    All session-related kwargs (``secret_key``, ``session_cookie``,
    ``max_age``, ``same_site``, ``https_only``, ``domain``, ``path``,
    ``**session_extras``) are forwarded verbatim to
    :func:`configure_user_session`. Each one defaults to ``None`` and
    falls back to the matching field on :class:`UserSessionSettings`
    (``app.pyhx.sessions_*``) when not overridden — see its docstring
    for semantics.

    Login methods
    -------------
    ``login_methods`` lists what the login page offers, in order. Defaults
    to ``[PasswordLogin()]`` (username and password, as before). Add
    :class:`EmailTokenLogin` for a link and code sent by email, or pass it
    alone to offer only that. Email login keys its stored hashes with the
    session's secret key.

    Each method has its own page, ``{login_path}?method=<key>``
    (``password``, ``email``); with more than one method, each page links to
    ``?method=select``, which lists the methods. ``default_login_method``
    sets what ``{login_path}`` without ``?method`` shows: the page of a
    configured method, given by its class (e.g. ``EmailTokenLogin``), or
    ``None`` for the list of methods. Omitted, it's the first method.

    Default pages
    -------------
    The login pages use ``login_page_template``; by default the app's own
    ``default_page_template`` (an ``AppShell`` without navigation and user
    menu), so they match the app's design. When ``include_default_pages``
    is true (default), this also registers:

    - ``GET {login_path}`` — a minimal username/password sign-in page.
    - ``POST {login_path}`` — verifies credentials via
      :meth:`UsersRepository.authenticate` and, on success, calls
      :func:`login_user` and redirects to a safe ``?next=`` URL or
      ``post_login_redirect``. On failure, redirects back to the
      login page with ``?error=invalid_credentials`` (preserving
      ``next``).
    - ``GET {logout_path}`` — calls :func:`logout_user` and redirects
      to ``post_logout_redirect``.
    - With :class:`EmailTokenLogin`: ``{login_path}/code`` (enter the
      code) and ``{login_path}/token`` (the link from the email).

    Apps that ship their own auth UI pass ``include_default_pages=False``.

    Exception handler
    -----------------
    When ``include_exception_handler`` is true (default), any
    :class:`NotAuthenticated` raised from a handler or dependency is
    converted into a redirect to ``login_path`` with the original URL
    captured in ``?next=`` — 303 + ``Location`` for normal requests,
    200 + ``HX-Redirect`` for HTMX requests (detected via the
    ``HX-Request: true`` header).

    The handler is registered **independently of**
    ``include_default_pages`` — apps that turn off the bundled pages
    keep this behaviour, but they MUST configure ``login_path`` to
    point at their own login page or the redirect will land on a 404.
    """
    login_methods = (
        list(login_methods) if login_methods is not None else [PasswordLogin()]
    )
    if not login_methods:
        raise ValueError("`login_methods` must name at least one login method.")

    default_key: str | None
    if isinstance(default_login_method, Omit):
        default_key = login_methods[0].key
    elif default_login_method is None:
        default_key = None
    elif default_login_method is not LoginMethod and any(
        isinstance(method, default_login_method) for method in login_methods
    ):
        default_key = default_login_method.key
    else:
        raise ValueError(
            f"`default_login_method` {default_login_method.__name__} is not one of "
            "the configured `login_methods`."
        )

    resolved_secret_key = configure_user_session(
        webapp,
        users=users,
        secret_key=secret_key,
        session_cookie=session_cookie,
        max_age=max_age,
        same_site=same_site,
        https_only=https_only,
        domain=domain,
        path=path,
        **session_extras,
    )

    if include_default_pages:
        register_default_auth_pages(
            webapp,
            users=users,
            login_methods=login_methods,
            secret_key=resolved_secret_key,
            login_page_template=login_page_template
            or default_login_page_template(webapp),
            default_login_method=default_key,
            login_path=login_path,
            logout_path=logout_path,
            post_login_redirect=post_login_redirect,
            post_logout_redirect=post_logout_redirect,
        )

    if include_exception_handler:
        handler = make_not_authenticated_handler(login_path)
        webapp.configure_fast_api_app(
            lambda app: app.add_exception_handler(NotAuthenticated, handler)
        )
