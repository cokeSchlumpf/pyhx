"""Session middleware + helpers for the user-authentication addon.

The cookie-backed session layer that turns the signed ``pyhx_session``
cookie set by :class:`starlette.middleware.sessions.SessionMiddleware`
into a populated :attr:`pyhx.core.RequestContext.user` on every
HTTP / WebSocket scope.
"""

import asyncio
import logging
import secrets
from typing import Any, Literal, cast

from commons.settings import read_settings_object
from commons.users import User, UsersRepository
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send

from pyhx.core import WebApp

LOG = logging.getLogger(__package__)

SESSION_USER_ID_KEY = "user_id"

_MISSING_SECRET_KEY_MESSAGE = (
    "PyHX user-session secret key is missing. "
    "Configure a real key under `app.pyhx.sessions_secret_key` in "
    "`~/.kpmg_apps/settings.toml`, `settings.toml`, or `pyproject.toml`, "
    "or set `APP__PYHX__SESSIONS_SECRET_KEY`. "
)


SameSite = Literal["lax", "strict", "none"]


class UserSessionSettings:
    """Settings for the user-session addon.

    Read from the merged settings tree at ``app.pyhx.*`` — see
    :mod:`commons.settings`. Every field except ``sessions_secret_key``
    has a sensible deployment-friendly default, so a minimal config
    only needs to provide the secret.

    TOML::

        [app.pyhx]
        sessions_secret_key = "<32+ random bytes, hex or base64>"
        sessions_cookie_name = "pyhx_session"
        sessions_max_age = 1209600           # 14 days, in seconds
        sessions_same_site = "lax"           # "lax" | "strict" | "none"
        sessions_https_only = false          # set true in prod
        sessions_domain = ""                 # empty = no domain restriction
        sessions_path = "/"

    Env var overrides follow the standard pattern
    (``APP__PYHX__SESSIONS_SECRET_KEY``, ``APP__PYHX__SESSIONS_HTTPS_ONLY``,
    …).

    Accessing :attr:`sessions_secret_key` raises ``RuntimeError`` if the
    value is unset or left at the placeholder ``"xxx"``. Callers decide
    how to handle that (e.g. :func:`configure_user_session` generates a
    random per-process key in dev mode and re-raises in prod).
    """

    def __init__(
        self,
        sessions_secret_key: str = "",
        sessions_cookie_name: str = "pyhx_session",
        sessions_max_age: int = 14 * 24 * 60 * 60,
        sessions_same_site: SameSite = "lax",
        sessions_https_only: bool = False,
        sessions_domain: str | None = None,
        sessions_path: str = "/",
        **_kwargs: Any,
    ) -> None:
        self._sessions_secret_key = sessions_secret_key
        self.sessions_cookie_name = sessions_cookie_name
        self.sessions_max_age = sessions_max_age
        self.sessions_same_site = sessions_same_site
        self.sessions_https_only = sessions_https_only
        # An empty string in TOML for ``sessions_domain`` reads more
        # naturally than ``"null"`` / leaving the key out; map it back to
        # ``None`` so callers get the Starlette-native "no Domain attr".
        self.sessions_domain = sessions_domain or None
        self.sessions_path = sessions_path

    @property
    def sessions_secret_key(self) -> str:
        if not self._sessions_secret_key or self._sessions_secret_key == "xxx":
            raise RuntimeError(_MISSING_SECRET_KEY_MESSAGE)
        return self._sessions_secret_key

    @staticmethod
    def read() -> "UserSessionSettings":
        return read_settings_object("pyhx", UserSessionSettings)


class CookieUserSession:
    """ASGI middleware that resolves the current ``User`` from the session
    cookie populated by Starlette's :class:`SessionMiddleware`.

    Reads ``scope["session"][SESSION_USER_ID_KEY]`` (set via :func:`login_user`),
    loads the matching ``RegisteredUser`` via ``users.find_user_by_id``,
    and writes it to ``scope["state"]["user"]`` so PyHX's RequestContext
    builders pick it up.

    Must run *inside* ``SessionMiddleware``. Use :func:`configure_user_session`
    to wire both layers in the correct order.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        users: UsersRepository,
        session_key: str = SESSION_USER_ID_KEY,
    ) -> None:
        self.app = app
        self.users = users
        self.session_key = session_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            session = scope.get("session") or {}
            user_id = session.get(self.session_key)
            if user_id:
                user = await asyncio.to_thread(self.users.find_user_by_id, user_id)
                if user is not None:
                    scope.setdefault("state", {})
                    scope["state"]["user"] = user
        await self.app(scope, receive, send)


def login_user(connection: HTTPConnection, user: User) -> None:
    """Mark this session as belonging to ``user``. Call from a login
    handler after verifying credentials. Works with both ``Request`` and
    ``WebSocket`` (anything that exposes ``.session``).

    Note that WebSocket handshakes don't emit a ``Set-Cookie`` response,
    so calling this from a WS handler is a no-op for the cookie itself —
    login is always an HTTP concern.
    """
    connection.session[SESSION_USER_ID_KEY] = str(user.id)


def logout_user(connection: HTTPConnection) -> None:
    """Clear the user from this session."""
    connection.session.pop(SESSION_USER_ID_KEY, None)


def configure_user_session(
    webapp: WebApp,
    *,
    users: UsersRepository,
    secret_key: str | None = None,
    session_cookie: str | None = None,
    max_age: int | None = None,
    same_site: SameSite | None = None,
    https_only: bool | None = None,
    domain: str | None = None,
    path: str | None = None,
    **session_extras: Any,
) -> None:
    """Wire :class:`CookieUserSession` + Starlette's ``SessionMiddleware``
    on ``webapp``.

    Every cookie-shape kwarg (``secret_key``, ``session_cookie``,
    ``max_age``, ``same_site``, ``https_only``, ``domain``, ``path``)
    defaults to ``None`` and falls back to the corresponding field on
    :class:`UserSessionSettings` (read from ``app.pyhx.*``). Pass an
    explicit value to override the settings without touching config —
    typical for tests, scripts, or apps that bring their own config
    mechanism.

    Because ``None`` always means "use settings", callers cannot force
    a value back to ``None`` (e.g. clearing ``domain`` when settings
    set it) — set the override explicitly via TOML / env instead.

    ``secret_key`` is special: if both the override and the setting
    are missing, behaviour diverges by ``webapp.is_dev``:

    - In dev mode, a random per-process key is generated and a warning
      is logged. Sessions don't survive a restart, but the addon stays
      usable without any config.
    - In prod mode, a ``RuntimeError`` is raised — refusing to start
      with an ephemeral key prevents silently signing real sessions
      with a key that vanishes on the next deploy or worker rotation.

    Order matters: ``SessionMiddleware`` must wrap ``CookieUserSession``
    so that ``scope["session"]`` is populated by the time
    ``CookieUserSession`` reads it. FastAPI's ``add_middleware`` inserts
    at position 0 (last added = outermost), so we add ``CookieUserSession``
    first.
    """
    settings = UserSessionSettings.read()

    if secret_key is None:
        try:
            secret_key = settings.sessions_secret_key
        except RuntimeError:
            if not webapp.is_dev:
                raise
            secret_key = secrets.token_urlsafe(32)
            LOG.warning(
                "PyHX user-session secret key is not configured; using a "
                "random per-process key (dev mode). Sessions will not "
                "survive process restart and won't be shared across "
                "workers. Configure `app.pyhx.sessions_secret_key` (or "
                "`APP__PYHX__SESSIONS_SECRET_KEY`) before deploying."
            )

    if session_cookie is None:
        session_cookie = settings.sessions_cookie_name
    if max_age is None:
        max_age = settings.sessions_max_age
    if same_site is None:
        same_site = cast(SameSite, settings.sessions_same_site)
    if https_only is None:
        https_only = settings.sessions_https_only
    if domain is None:
        domain = settings.sessions_domain
    if path is None:
        path = settings.sessions_path

    def configure_middleware(app: FastAPI) -> None:
        app.add_middleware(CookieUserSession, users=users)
        app.add_middleware(
            SessionMiddleware,
            secret_key=secret_key,
            session_cookie=session_cookie,
            max_age=max_age,
            same_site=same_site,
            https_only=https_only,
            domain=domain,
            path=path,
            **session_extras,
        )

    webapp.configure_fast_api_app(configure_middleware)
