import logging
from dataclasses import dataclass

import htpy as y
import pytest
from commons.users import (
    AnonymousUser,
    AuthenticatedUser,
    RegisteredUser,
    SQLUsersRepository,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from pyhx.addons.user_authentication import (
    CookieUserSession,
    NotAuthenticated,
    UserSessionSettings,
    configure_user_authentication,
    configure_user_session,
    require_user,
    login_user,
    logout_user,
    require_authenticated_user,
    require_registered_user,
)
from pyhx.core.request_context import RequestContext, set_request_context
from pyhx.core.webapp import WebApp


TEST_SECRET = "test-secret-key-do-not-use-in-prod"


@dataclass
class _Captured:
    ctx: RequestContext | None = None


def _make_repo() -> SQLUsersRepository:
    """Fresh in-memory SQLite repo. Uses ``StaticPool`` so every SQLAlchemy
    session reuses the same underlying connection — without it, each new
    connection to ``:memory:`` opens its own empty database and tables
    created by ``create_all`` are invisible to subsequent queries."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return SQLUsersRepository(engine)


def _make_user(repo: SQLUsersRepository, username: str = "jane") -> RegisteredUser:
    user = RegisteredUser.create(
        username=username,
        password_hash=repo.hash_password("pw"),
        display_name=f"{username.title()} Doe",
    )
    return repo.upsert_user(user)


def _build_app(
    captured: _Captured,
    repo: SQLUsersRepository,
    *,
    login_target: RegisteredUser | None = None,
) -> tuple[WebApp, TestClient]:
    """Build a WebApp with three routes: a probe that captures the current
    context, a login endpoint that marks the session as the given user,
    and a logout endpoint."""

    hx = WebApp()

    @hx.fragment.get("/probe")
    async def probe() -> y.Node:
        captured.ctx = RequestContext.get()
        return y.div["ok"]

    if login_target is not None:

        @hx.fragment.post("/login")
        async def do_login() -> y.Node:
            ctx = RequestContext.get()
            assert ctx.request is not None
            login_user(ctx.request, login_target)
            return y.div["logged-in"]

        @hx.fragment.post("/logout")
        async def do_logout() -> y.Node:
            ctx = RequestContext.get()
            assert ctx.request is not None
            logout_user(ctx.request)
            return y.div["logged-out"]

    configure_user_session(hx, users=repo, secret_key=TEST_SECRET, https_only=False)
    app = hx.create_app()
    return hx, TestClient(app)


class TestRequestContextWiring:
    def test_anonymous_when_no_session_cookie(self):
        captured = _Captured()
        repo = _make_repo()
        _, client = _build_app(captured, repo)

        response = client.get("/probe")

        assert response.status_code == 200
        ctx = captured.ctx
        assert ctx is not None
        assert isinstance(ctx.user, AnonymousUser)

    def test_login_round_trip_authenticates_subsequent_requests(self):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        _, client = _build_app(captured, repo, login_target=user)

        login_resp = client.post("/login")
        assert login_resp.status_code == 200

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        # The loaded instance may be a fresh SQLAlchemy row, so compare by id.
        assert isinstance(captured.ctx.user, RegisteredUser)
        assert captured.ctx.user.id == user.id

    def test_logout_clears_user(self):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        _, client = _build_app(captured, repo, login_target=user)

        client.post("/login")
        client.post("/logout")

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        assert isinstance(captured.ctx.user, AnonymousUser)

    def test_unknown_user_id_falls_back_to_anonymous(self):
        """User logs in, then is deleted from the repo. The cookie still
        carries the user_id, but lookup returns ``None`` → handler sees
        an anonymous context, no exception bubbles."""
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        _, client = _build_app(captured, repo, login_target=user)

        client.post("/login")
        repo.delete_user(user)

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        assert isinstance(captured.ctx.user, AnonymousUser)


class TestMiddlewareOrdering:
    def test_configure_user_session_puts_session_middleware_outside(self):
        """SessionMiddleware must wrap CookieUserSession so that
        ``scope["session"]`` exists by the time the inner middleware
        reads it. Guards against future regressions if someone
        "fixes" the order."""
        hx = WebApp()
        configure_user_session(hx, users=_make_repo(), secret_key=TEST_SECRET)
        app = hx.create_app()

        # Starlette's add_middleware inserts at position 0, so the last-added
        # middleware is at index 0 (outermost).
        middleware_classes = [mw.cls for mw in app.user_middleware]
        assert middleware_classes[0] is SessionMiddleware
        assert middleware_classes[1] is CookieUserSession


class TestUserSessionSettings:
    def test_value_passed_directly_is_returned(self):
        settings = UserSessionSettings(sessions_secret_key="abc")
        assert settings.sessions_secret_key == "abc"

    def test_missing_value_raises_with_helpful_message(self):
        settings = UserSessionSettings()
        with pytest.raises(RuntimeError) as excinfo:
            _ = settings.sessions_secret_key
        msg = str(excinfo.value)
        assert "app.pyhx.sessions_secret_key" in msg
        assert "APP__PYHX__SESSIONS_SECRET_KEY" in msg

    def test_placeholder_value_xxx_is_treated_as_unset(self):
        settings = UserSessionSettings(sessions_secret_key="xxx")
        with pytest.raises(RuntimeError):
            _ = settings.sessions_secret_key

    def test_unknown_kwargs_are_silently_ignored(self):
        """Forward-compat: future sibling settings keys (e.g. csrf_secret_key)
        under ``[app.pyhx]`` shouldn't break instantiation of this class."""
        settings = UserSessionSettings(
            sessions_secret_key="abc", csrf_secret_key="other"  # type: ignore[call-arg]
        )
        assert settings.sessions_secret_key == "abc"

    def test_cookie_attribute_defaults(self):
        """Defaults are dev-friendly: not HTTPS-only, lax SameSite, no
        Domain restriction, root Path, the standard 14-day max age."""
        settings = UserSessionSettings()
        assert settings.sessions_cookie_name == "pyhx_session"
        assert settings.sessions_max_age == 14 * 24 * 60 * 60
        assert settings.sessions_same_site == "lax"
        assert settings.sessions_https_only is False
        assert settings.sessions_domain is None
        assert settings.sessions_path == "/"

    def test_cookie_attributes_can_be_overridden(self):
        settings = UserSessionSettings(
            sessions_cookie_name="my_app",
            sessions_max_age=3600,
            sessions_same_site="strict",
            sessions_https_only=True,
            sessions_domain="example.com",
            sessions_path="/admin",
        )
        assert settings.sessions_cookie_name == "my_app"
        assert settings.sessions_max_age == 3600
        assert settings.sessions_same_site == "strict"
        assert settings.sessions_https_only is True
        assert settings.sessions_domain == "example.com"
        assert settings.sessions_path == "/admin"

    def test_empty_string_domain_normalises_to_none(self):
        """TOML reads more naturally with an empty string than ``null``;
        the constructor maps it back to ``None`` so callers get
        Starlette's "no Domain attribute" behaviour."""
        settings = UserSessionSettings(sessions_domain="")
        assert settings.sessions_domain is None


class TestConfigureUserSessionFromSettings:
    """The cookie-shape kwargs of ``configure_user_session`` fall back to
    :class:`UserSessionSettings` fields when left as their default
    ``None``. Tests verify the wiring; we read back the registered
    ``SessionMiddleware`` kwargs from the FastAPI app to assert."""

    def _read_session_middleware_kwargs(self, monkeypatch, **settings_kwargs):
        """Configure a WebApp using ``settings_kwargs`` as the patched
        :meth:`UserSessionSettings.read` and return the kwargs the
        ``SessionMiddleware`` was registered with."""
        monkeypatch.delenv("APP__PYHX__SESSIONS_SECRET_KEY", raising=False)
        monkeypatch.setattr(
            "pyhx.addons.user_authentication.UserSessionSettings.read",
            lambda: UserSessionSettings(
                sessions_secret_key=TEST_SECRET, **settings_kwargs
            ),
        )
        hx = WebApp()
        configure_user_session(hx, users=_make_repo())
        app = hx.create_app()
        session_mw = next(
            mw for mw in app.user_middleware if mw.cls is SessionMiddleware
        )
        return session_mw.kwargs

    def test_settings_provide_cookie_name(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_cookie_name="my_app_session"
        )
        assert kwargs["session_cookie"] == "my_app_session"

    def test_settings_provide_max_age(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_max_age=3600
        )
        assert kwargs["max_age"] == 3600

    def test_settings_provide_same_site(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_same_site="strict"
        )
        assert kwargs["same_site"] == "strict"

    def test_settings_provide_https_only(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_https_only=True
        )
        assert kwargs["https_only"] is True

    def test_settings_provide_domain(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_domain="example.com"
        )
        assert kwargs["domain"] == "example.com"

    def test_settings_provide_path(self, monkeypatch):
        kwargs = self._read_session_middleware_kwargs(
            monkeypatch, sessions_path="/admin"
        )
        assert kwargs["path"] == "/admin"

    def test_explicit_param_overrides_settings(self, monkeypatch):
        """An explicit kwarg wins over the matching settings field."""
        monkeypatch.delenv("APP__PYHX__SESSIONS_SECRET_KEY", raising=False)
        monkeypatch.setattr(
            "pyhx.addons.user_authentication.UserSessionSettings.read",
            lambda: UserSessionSettings(
                sessions_secret_key=TEST_SECRET,
                sessions_cookie_name="settings_value",
                sessions_https_only=False,
            ),
        )
        hx = WebApp()
        configure_user_session(
            hx,
            users=_make_repo(),
            session_cookie="explicit_value",
            https_only=True,
        )
        app = hx.create_app()
        session_mw = next(
            mw for mw in app.user_middleware if mw.cls is SessionMiddleware
        )
        assert session_mw.kwargs["session_cookie"] == "explicit_value"
        assert session_mw.kwargs["https_only"] is True


class TestConfigureUserSessionMissingKey:
    """When no ``secret_key`` is passed and settings don't provide one,
    behavior diverges by ``webapp.is_dev``."""

    def test_dev_mode_generates_random_key_and_logs_warning(
        self, monkeypatch, caplog
    ):
        # Make sure no real config provides the key.
        monkeypatch.delenv("APP__PYHX__SESSIONS_SECRET_KEY", raising=False)
        monkeypatch.setattr(
            "pyhx.addons.user_authentication.UserSessionSettings.read",
            lambda: UserSessionSettings(),
        )

        hx = WebApp(is_dev=True)
        with caplog.at_level(logging.WARNING, logger="pyhx.addons.user_authentication"):
            configure_user_session(hx, users=_make_repo())

        # The addon must keep working — building the app should succeed.
        hx.create_app()
        assert any(
            "random per-process key" in record.message
            for record in caplog.records
        )

    def test_prod_mode_raises(self, monkeypatch):
        monkeypatch.delenv("APP__PYHX__SESSIONS_SECRET_KEY", raising=False)
        monkeypatch.setattr(
            "pyhx.addons.user_authentication.UserSessionSettings.read",
            lambda: UserSessionSettings(),
        )

        hx = WebApp(is_dev=False)
        with pytest.raises(RuntimeError) as excinfo:
            configure_user_session(hx, users=_make_repo())
        assert "app.pyhx.sessions_secret_key" in str(excinfo.value)

    def test_explicit_secret_key_skips_settings_lookup_in_prod(self):
        """Passing an explicit key must not trigger the settings read,
        so ops can use a custom secret source without setting up a TOML."""
        hx = WebApp(is_dev=False)
        # No monkeypatching of settings — this must not raise.
        configure_user_session(hx, users=_make_repo(), secret_key=TEST_SECRET)
        hx.create_app()


class TestCookieUserSessionUnit:
    def test_websocket_scope_with_session_loads_user(self):
        """Drive CookieUserSession directly with a synthetic WS scope so we
        cover the WS branch even though the current WebApp WS handler stub
        doesn't expose anything to capture."""
        repo = _make_repo()
        user = _make_user(repo)

        inner_received: dict[str, dict | None] = {"state": None}

        async def inner(scope, receive, send):
            inner_received["state"] = scope.get("state")

        mw = CookieUserSession(inner, users=repo)
        scope = {
            "type": "websocket",
            "session": {"user_id": user.id},
        }

        async def noop_receive():
            return {"type": "websocket.disconnect"}

        async def noop_send(message):
            pass

        import asyncio

        asyncio.run(mw(scope, noop_receive, noop_send))

        state = inner_received["state"]
        assert state is not None
        assert isinstance(state["user"], RegisteredUser)
        assert state["user"].id == user.id

    def test_websocket_scope_without_session_passes_through(self):
        async def inner(scope, receive, send):
            pass

        mw = CookieUserSession(inner, users=_make_repo())
        scope = {"type": "websocket"}  # no session key at all

        async def noop_receive():
            return {"type": "websocket.disconnect"}

        async def noop_send(message):
            pass

        import asyncio

        # Must not raise.
        asyncio.run(mw(scope, noop_receive, noop_send))

    def test_lifespan_scope_is_passed_through_untouched(self):
        seen: list[str] = []

        async def inner(scope, receive, send):
            seen.append(scope["type"])

        mw = CookieUserSession(inner, users=_make_repo())

        async def noop_receive():
            return {}

        async def noop_send(message):
            pass

        import asyncio

        asyncio.run(mw({"type": "lifespan"}, noop_receive, noop_send))
        assert seen == ["lifespan"]


def _build_app_with_auth(
    captured: _Captured,
    repo: SQLUsersRepository,
    **auth_kwargs,
) -> TestClient:
    """WebApp with a /probe fragment and the default auth pages wired via
    ``configure_user_authentication``. Extra kwargs forwarded to the
    configure call so individual tests can flip ``include_default_pages``
    or override paths."""
    hx = WebApp()

    @hx.fragment.get("/probe")
    async def probe() -> y.Node:
        captured.ctx = RequestContext.get()
        return y.div["ok"]

    configure_user_authentication(
        hx,
        users=repo,
        secret_key=TEST_SECRET,
        https_only=False,
        **auth_kwargs,
    )
    return TestClient(hx.create_app(), follow_redirects=False)


# DataForm picks its submit URL from the form name passed to
# ``DataForm("app-login", ...)`` inside ``register_default_auth_pages``.
# The pattern is documented in ``DataForm.__init__`` and stable; we
# hardcode here so a future rename of the form is caught by these tests.
LOGIN_SUBMIT_URL = "/_components/data-form/app-login/submit"


def _post_login(
    client: TestClient,
    username: str,
    password: str,
    *,
    next_: str = "",
    submit_url: str = LOGIN_SUBMIT_URL,
):
    return client.post(
        submit_url,
        data={"username": username, "password": password, "next": next_},
    )


class TestDefaultAuthPages:
    def test_get_login_renders_form(self):
        captured = _Captured()
        repo = _make_repo()
        client = _build_app_with_auth(captured, repo)

        resp = client.get("/login")

        assert resp.status_code == 200
        body = resp.text
        assert 'name="username"' in body
        assert 'name="password"' in body
        # DataForm wires the submit endpoint via hx-post on the <form> tag.
        assert f'hx-post="{LOGIN_SUBMIT_URL}"' in body

    def test_get_login_propagates_next_into_hidden_input(self):
        captured = _Captured()
        repo = _make_repo()
        client = _build_app_with_auth(captured, repo)

        resp = client.get("/login?next=/dashboard")

        assert resp.status_code == 200
        body = resp.text
        assert 'name="next"' in body
        assert 'value="/dashboard"' in body

    def test_post_login_with_valid_credentials_sets_session_and_returns_hx_redirect(
        self,
    ):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(captured, repo)

        resp = _post_login(client, user.username, "pw")

        # DataForm submit goes through htmx, so the redirect is signalled
        # by HX-Redirect on a 200, not a 3xx + Location.
        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == "/"
        assert resp.text == ""

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        assert isinstance(captured.ctx.user, RegisteredUser)
        assert captured.ctx.user.id == user.id

    def test_post_login_honours_safe_next(self):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(captured, repo)

        resp = _post_login(client, user.username, "pw", next_="/dashboard")

        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == "/dashboard"

    @pytest.mark.parametrize(
        "unsafe_next",
        [
            "https://evil.example/x",
            "//evil.example/x",
            "javascript:alert(1)",
            "dashboard",
        ],
    )
    def test_post_login_rejects_unsafe_next(self, unsafe_next):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(captured, repo)

        resp = _post_login(client, user.username, "pw", next_=unsafe_next)

        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == "/"

    def test_post_login_with_invalid_credentials_renders_form_and_does_not_set_session(
        self,
    ):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(captured, repo)

        resp = _post_login(client, user.username, "wrong")

        # No redirect — the body carries an OOB swap that re-renders the
        # form together with a notification.
        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") is None
        body = resp.text
        assert "Invalid username or password" in body
        assert "hx-data-form__app-login" in body

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        assert isinstance(captured.ctx.user, AnonymousUser)

    def test_get_logout_clears_session_and_redirects(self):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(captured, repo)

        _post_login(client, user.username, "pw")

        logout_resp = client.get("/logout")
        assert logout_resp.status_code == 303
        assert logout_resp.headers["location"] == "/login"

        probe_resp = client.get("/probe")
        assert probe_resp.status_code == 200
        assert captured.ctx is not None
        assert isinstance(captured.ctx.user, AnonymousUser)

    def test_include_default_pages_false_skips_registration(self):
        captured = _Captured()
        repo = _make_repo()
        client = _build_app_with_auth(captured, repo, include_default_pages=False)

        assert client.get("/login").status_code == 404
        # DataForm's submit endpoint shouldn't exist either when the
        # default pages aren't wired.
        assert client.post(LOGIN_SUBMIT_URL, data={}).status_code == 404
        assert client.get("/logout").status_code == 404

    def test_custom_paths_override_defaults(self):
        captured = _Captured()
        repo = _make_repo()
        user = _make_user(repo)
        client = _build_app_with_auth(
            captured,
            repo,
            login_path="/sign-in",
            logout_path="/sign-out",
            post_logout_redirect="/sign-in",
        )

        assert client.get("/login").status_code == 404
        assert client.get("/sign-in").status_code == 200

        # The DataForm name is fixed, so its submit endpoint URL stays the
        # same even when ``login_path`` changes.
        resp = _post_login(client, user.username, "pw")
        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == "/"

        logout_resp = client.get("/sign-out")
        assert logout_resp.status_code == 303
        assert logout_resp.headers["location"] == "/sign-in"


def _build_app_with_protected_route(
    *,
    protected_path: str = "/protected",
    **auth_kwargs,
) -> TestClient:
    """WebApp that exposes a single page which always raises
    :class:`NotAuthenticated`. ``auth_kwargs`` are forwarded to
    ``configure_user_authentication`` so tests can flip
    ``include_exception_handler`` or override ``login_path``."""
    hx = WebApp()

    @hx.page(protected_path, title="Protected")
    async def protected() -> y.Node:
        raise NotAuthenticated()

    configure_user_authentication(
        hx,
        users=_make_repo(),
        secret_key=TEST_SECRET,
        https_only=False,
        **auth_kwargs,
    )
    return TestClient(hx.create_app(), follow_redirects=False)


class TestNotAuthenticatedHandler:
    def test_non_htmx_request_gets_303_to_login_with_next(self):
        client = _build_app_with_protected_route()

        resp = client.get("/protected")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/login?next=%2Fprotected"
        assert resp.headers.get("HX-Redirect") is None

    def test_htmx_request_gets_hx_redirect(self):
        client = _build_app_with_protected_route()

        resp = client.get("/protected", headers={"HX-Request": "true"})

        # HTMX needs 200 + HX-Redirect — XHR follows 3xx transparently
        # and would otherwise swap the login page's body.
        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == "/login?next=%2Fprotected"
        assert resp.headers.get("location") is None

    def test_next_preserves_query_string(self):
        client = _build_app_with_protected_route()

        resp = client.get("/protected?tab=billing&sort=desc")

        assert resp.status_code == 303
        # Query string is encoded into the next= value.
        assert resp.headers["location"] == (
            "/login?next=%2Fprotected%3Ftab%3Dbilling%26sort%3Ddesc"
        )

    def test_no_loop_when_raised_on_login_path(self):
        # Stand up a fragment at /login that raises — the loop guard
        # should kick in and emit a bare ``/login`` redirect without next.
        hx = WebApp()

        @hx.page("/login", title="Login")
        async def fake_login() -> y.Node:
            raise NotAuthenticated()

        configure_user_authentication(
            hx,
            users=_make_repo(),
            secret_key=TEST_SECRET,
            https_only=False,
            include_default_pages=False,
        )
        client = TestClient(hx.create_app(), follow_redirects=False)

        resp = client.get("/login")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/login"

    def test_custom_login_path_is_used_for_redirect(self):
        client = _build_app_with_protected_route(
            login_path="/sign-in",
            include_default_pages=False,
        )

        resp = client.get("/protected")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/sign-in?next=%2Fprotected"

    def test_include_exception_handler_false_lets_exception_propagate(self):
        # With the handler turned off, the WebApp's in-route catch-all
        # falls back to its debug page (500 + stacktrace HTML).
        client = _build_app_with_protected_route(
            include_exception_handler=False,
        )

        resp = client.get("/protected")

        assert resp.status_code == 500
        assert resp.headers.get("location") is None
        assert resp.headers.get("HX-Redirect") is None
        assert "NotAuthenticated" in resp.text


def _set_user(user) -> None:
    """Replace the request context for the current test with one whose
    ``user`` is ``user``. The ContextVar leaks between tests, so every
    accessor test calls this first to establish a known state."""
    set_request_context(RequestContext(user=user))


def _make_authenticated_user(display_name: str = "Ext User") -> AuthenticatedUser:
    return AuthenticatedUser.create(display_name=display_name)


class TestUserAccessors:
    def test_get_user_returns_anonymous_when_context_has_no_session(self):
        _set_user(AnonymousUser())

        result = require_user()

        assert isinstance(result, AnonymousUser)

    def test_get_user_returns_the_signed_in_user(self):
        repo = _make_repo()
        user = _make_user(repo)
        _set_user(user)

        result = require_user()

        assert result is user

    def test_require_user_returns_registered_user(self):
        repo = _make_repo()
        user = _make_user(repo)
        _set_user(user)

        assert require_authenticated_user() is user

    def test_require_user_returns_externally_authenticated_user(self):
        ext = _make_authenticated_user()
        _set_user(ext)

        assert require_authenticated_user() is ext

    def test_require_user_raises_for_anonymous(self):
        _set_user(AnonymousUser())

        with pytest.raises(NotAuthenticated):
            require_authenticated_user()

    def test_require_registered_user_returns_registered_user(self):
        repo = _make_repo()
        user = _make_user(repo)
        _set_user(user)

        assert require_registered_user() is user

    def test_require_registered_user_raises_for_anonymous(self):
        _set_user(AnonymousUser())

        with pytest.raises(NotAuthenticated):
            require_registered_user()

    def test_require_registered_user_raises_for_externally_authenticated_user(self):
        _set_user(_make_authenticated_user())

        with pytest.raises(NotAuthenticated):
            require_registered_user()
