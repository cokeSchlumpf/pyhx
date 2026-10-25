from dataclasses import dataclass, field

import htpy as y
import pytest
from commons.users import AnonymousUser, RegisteredUser, SQLUsersRepository
from commons.users.login_tokens import (
    InMemoryLoginTokenStore,
    LoginTokenMessage,
    LoginTokenSettings,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from pyhx.addons.user_authentication import (
    EmailTokenLogin,
    PasswordLogin,
    _session,
    configure_user_authentication,
)
from pyhx.core.request_context import RequestContext
from pyhx.core.webapp import WebApp
from pyhx.page_templates import AppShell, CanvasShell

TEST_SECRET = "test-secret-key-do-not-use-in-prod"
EMAIL_SUBMIT_URL = "/_components/data-form/app-login-email/submit"
CODE_SUBMIT_URL = "/_components/data-form/app-login-code/submit"
PASSWORD_SUBMIT_URL = "/_components/data-form/app-login/submit"


@dataclass
class CollectingSender:
    messages: list[LoginTokenMessage] = field(default_factory=list)

    def send_login_token(self, message: LoginTokenMessage) -> None:
        self.messages.append(message)

    @property
    def last(self) -> LoginTokenMessage:
        return self.messages[-1]


class FailingSender:
    def send_login_token(self, message: LoginTokenMessage) -> None:
        raise ConnectionError("SMTP down")


@dataclass
class App:
    client: TestClient
    sender: CollectingSender
    hx: WebApp
    seen: list[object] = field(default_factory=list)

    def current_user(self, client: TestClient | None = None) -> object:
        (client or self.client).get("/probe")
        return self.seen[-1]

    def new_client(self) -> TestClient:
        """A second browser: no cookies of the first."""
        return TestClient(self.hx.create_app(), follow_redirects=False)


def _repo() -> SQLUsersRepository:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repo = SQLUsersRepository(engine)
    repo.upsert_user(
        RegisteredUser.create(
            username="jane",
            password_hash=repo.hash_password("pw"),
            display_name="Jane Doe",
            email="jane@example.com",
        )
    )
    return repo


def _app(login_methods=None, sender=None) -> App:
    sender = sender if sender is not None else CollectingSender()
    hx = WebApp()
    seen: list[object] = []

    @hx.fragment.get("/probe")
    async def probe() -> y.Node:
        seen.append(RequestContext.get().user)
        return y.div["ok"]

    if login_methods is None:
        login_methods = [
            PasswordLogin(),
            EmailTokenLogin(
                store=InMemoryLoginTokenStore(),
                sender=sender,
                settings=LoginTokenSettings(),
                base_url="https://app.example.com",
            ),
        ]

    configure_user_authentication(
        hx,
        users=_repo(),
        login_methods=login_methods,
        secret_key=TEST_SECRET,
        https_only=False,
    )
    client = TestClient(hx.create_app(), follow_redirects=False)
    return App(client=client, sender=sender, hx=hx, seen=seen)


def _request_link(
    app: App, email: str = "jane@example.com", next_: str = "", client=None
):
    return (client or app.client).post(
        EMAIL_SUBMIT_URL, data={"email": email, "next": next_}
    )


def _token(app: App) -> str:
    return app.sender.last.link.split("t=", 1)[1]


def _wrong_code(app: App) -> str:
    return "000000" if app.sender.last.code != "000000" else "111111"


class TestLoginPage:
    def test_default_offers_password_only(self):
        hx = WebApp()
        configure_user_authentication(hx, users=_repo(), secret_key=TEST_SECRET)
        body = TestClient(hx.create_app()).get("/login").text

        assert 'name="password"' in body
        assert 'name="email"' not in body

    def test_without_method_shows_the_first_method(self):
        body = _app().client.get("/login").text

        assert 'name="password"' in body
        assert 'name="email"' not in body

    def test_method_parameter_selects_the_page(self):
        body = _app().client.get("/login?method=email").text

        assert 'name="email"' in body
        assert 'name="password"' not in body
        assert "<h1>Sign in</h1>" in body

    def test_method_pages_link_to_the_list_of_methods(self):
        body = _app().client.get("/login?method=email&next=/dossiers").text

        assert "Sign in with another method" in body
        assert 'href="/login?method=select&amp;next=%2Fdossiers"' in body

    def test_select_lists_every_method_and_keeps_next(self):
        body = _app().client.get("/login?method=select&next=/dossiers").text

        assert 'href="/login?method=password&amp;next=%2Fdossiers"' in body
        assert 'href="/login?method=email&amp;next=%2Fdossiers"' in body
        assert "Username and password" in body
        assert 'name="password"' not in body

    def test_default_none_starts_with_the_list_of_methods(self):
        hx = WebApp()
        configure_user_authentication(
            hx,
            users=_repo(),
            login_methods=[
                PasswordLogin(),
                EmailTokenLogin(settings=LoginTokenSettings()),
            ],
            default_login_method=None,
            secret_key=TEST_SECRET,
        )
        body = TestClient(hx.create_app()).get("/login").text

        assert "Choose how you want to sign in" in body
        assert 'name="password"' not in body

    def test_default_can_name_a_method(self):
        hx = WebApp()
        configure_user_authentication(
            hx,
            users=_repo(),
            login_methods=[
                PasswordLogin(),
                EmailTokenLogin(settings=LoginTokenSettings()),
            ],
            default_login_method=EmailTokenLogin,
            secret_key=TEST_SECRET,
        )
        body = TestClient(hx.create_app()).get("/login").text

        assert 'name="email"' in body

    def test_default_that_is_not_configured_is_rejected(self):
        with pytest.raises(ValueError, match="EmailTokenLogin is not one of"):
            configure_user_authentication(
                WebApp(),
                users=_repo(),
                login_methods=[PasswordLogin()],
                default_login_method=EmailTokenLogin,
                secret_key=TEST_SECRET,
            )

    def test_single_method_has_no_switch_link_and_no_list(self):
        hx = WebApp()
        configure_user_authentication(hx, users=_repo(), secret_key=TEST_SECRET)
        client = TestClient(hx.create_app())

        assert "Sign in with another method" not in client.get("/login").text
        assert 'name="password"' in client.get("/login?method=select").text

    def test_unknown_method_falls_back_to_the_default(self):
        body = _app().client.get("/login?method=nope").text

        assert 'name="password"' in body

    def test_next_is_carried_into_the_form(self):
        body = _app().client.get("/login?method=email&next=/dossiers").text

        assert 'value="/dossiers"' in body

    def test_empty_login_methods_are_rejected(self):
        with pytest.raises(ValueError, match="at least one"):
            configure_user_authentication(
                WebApp(), users=_repo(), login_methods=[], secret_key=TEST_SECRET
            )

    def test_password_login_still_works_alongside(self):
        app = _app()
        resp = app.client.post(
            PASSWORD_SUBMIT_URL, data={"username": "jane", "password": "pw", "next": ""}
        )

        assert resp.headers.get("HX-Redirect") == "/"
        assert isinstance(app.current_user(), RegisteredUser)


class TestRequestLink:
    def test_known_address_gets_link_and_code_and_lands_on_code_page(self):
        app = _app()
        resp = _request_link(app)

        assert resp.headers.get("HX-Redirect") == "/login/code"
        assert app.sender.last.email == "jane@example.com"
        assert app.sender.last.link.startswith("https://app.example.com/login/token?t=")

    def test_unknown_address_lands_on_the_same_page_without_sending(self):
        app = _app()
        resp = _request_link(app, "nobody@example.com")

        assert resp.headers.get("HX-Redirect") == "/login/code"
        assert app.sender.messages == []

    def test_rate_limited_request_lands_on_the_same_page(self):
        app = _app()
        responses = [_request_link(app) for _ in range(4)]

        assert {r.headers.get("HX-Redirect") for r in responses} == {"/login/code"}
        assert len(app.sender.messages) == 3

    def test_send_failure_shows_an_error_and_stays_on_the_login_page(self):
        sender = FailingSender()
        app = _app(
            login_methods=[
                EmailTokenLogin(sender=sender, settings=LoginTokenSettings())
            ]
        )
        resp = _request_link(app)

        assert resp.headers.get("HX-Redirect") is None
        assert "could not be sent" in resp.text

    def test_link_uses_request_url_without_base_url(self):
        sender = CollectingSender()
        app = _app(
            login_methods=[
                EmailTokenLogin(sender=sender, settings=LoginTokenSettings())
            ]
        )
        _request_link(app)

        assert sender.last.link.startswith("http://testserver/login/token?t=")


class TestCode:
    def test_code_page_without_pending_request_redirects_to_login(self):
        resp = _app().client.get("/login/code")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/login"

    def test_code_page_after_request_shows_the_code_form(self):
        app = _app()
        _request_link(app)
        body = app.client.get("/login/code").text

        assert 'name="code"' in body
        assert 'autocomplete="one-time-code"' in body
        assert 'href="/login?method=email"' in body

    def test_right_code_logs_in_and_honours_next(self):
        app = _app()
        _request_link(app, next_="/dossiers")
        resp = app.client.post(CODE_SUBMIT_URL, data={"code": app.sender.last.code})

        assert resp.headers.get("HX-Redirect") == "/dossiers"
        assert isinstance(app.current_user(), RegisteredUser)

    def test_unsafe_next_falls_back_to_default(self):
        app = _app()
        _request_link(app, next_="https://evil.example/x")
        resp = app.client.post(CODE_SUBMIT_URL, data={"code": app.sender.last.code})

        assert resp.headers.get("HX-Redirect") == "/"

    def test_wrong_code_shows_neutral_message(self):
        app = _app()
        _request_link(app)
        resp = app.client.post(CODE_SUBMIT_URL, data={"code": _wrong_code(app)})

        assert resp.headers.get("HX-Redirect") is None
        assert "invalid or has expired" in resp.text
        assert isinstance(app.current_user(), AnonymousUser)

    def test_code_for_unknown_address_shows_the_same_message(self):
        app = _app()
        _request_link(app, "nobody@example.com")
        resp = app.client.post(CODE_SUBMIT_URL, data={"code": "123456"})

        assert "invalid or has expired" in resp.text

    def test_too_many_attempts_show_the_same_message(self):
        app = _app()
        _request_link(app)
        for _ in range(5):
            resp = app.client.post(CODE_SUBMIT_URL, data={"code": _wrong_code(app)})

        assert "invalid or has expired" in resp.text

    def test_code_only_works_in_the_requesting_browser(self):
        app = _app()
        _request_link(app)
        other = app.new_client()
        resp = other.post(CODE_SUBMIT_URL, data={"code": app.sender.last.code})

        assert resp.headers.get("HX-Redirect") is None
        assert isinstance(app.current_user(other), AnonymousUser)


class TestLink:
    def test_same_browser_logs_in_right_away(self):
        app = _app()
        _request_link(app, next_="/dossiers")
        resp = app.client.get(f"/login/token?t={_token(app)}")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dossiers"
        assert isinstance(app.current_user(), RegisteredUser)

    def test_other_browser_gets_a_confirmation_button_and_is_not_logged_in(self):
        app = _app()
        _request_link(app)
        other = app.new_client()
        resp = other.get(f"/login/token?t={_token(app)}")

        assert resp.status_code == 200
        assert 'hx-post="/login/token"' in resp.text
        assert isinstance(app.current_user(other), AnonymousUser)

    def test_confirming_in_another_browser_logs_in_once(self):
        app = _app()
        _request_link(app, next_="/dossiers")
        other = app.new_client()
        token = _token(app)

        first = other.post("/login/token", data={"t": token})
        second = app.new_client().post("/login/token", data={"t": token})

        assert first.headers.get("HX-Redirect") == "/dossiers"
        assert isinstance(app.current_user(other), RegisteredUser)
        assert second.headers.get("HX-Redirect") is None
        assert "invalid or has expired" in second.text

    def test_scanner_opening_the_link_does_not_consume_it(self):
        app = _app()
        _request_link(app)
        app.new_client().get(f"/login/token?t={_token(app)}")  # scanner, no session

        resp = app.client.get(f"/login/token?t={_token(app)}")

        assert resp.status_code == 303
        assert isinstance(app.current_user(), RegisteredUser)

    def test_used_link_shows_neutral_message_without_a_button(self):
        app = _app()
        _request_link(app)
        token = _token(app)
        app.client.get(f"/login/token?t={token}")  # redeemed in the requesting browser

        resp = app.new_client().get(f"/login/token?t={token}")

        assert "invalid or has expired" in resp.text
        assert 'hx-post="/login/token"' not in resp.text

    def test_unknown_link_shows_neutral_message(self):
        resp = _app().client.get("/login/token?t=not-a-token")

        assert resp.status_code == 200
        assert "invalid or has expired" in resp.text

    def test_redeeming_the_link_invalidates_the_code(self):
        app = _app()
        _request_link(app)
        code = app.sender.last.code
        app.new_client().post("/login/token", data={"t": _token(app)})

        resp = app.client.post(CODE_SUBMIT_URL, data={"code": code})
        assert "invalid or has expired" in resp.text


class TestSlidingSession:
    def _login(self, app: App) -> None:
        app.client.post(
            PASSWORD_SUBMIT_URL, data={"username": "jane", "password": "pw", "next": ""}
        )

    def test_cookie_is_renewed_after_the_interval(self, monkeypatch):
        app = _app()
        now = [1_000_000.0]
        monkeypatch.setattr(_session.time, "time", lambda: now[0])
        self._login(app)

        now[0] += _session.SESSION_RENEW_INTERVAL
        resp = app.client.get("/probe")

        assert "set-cookie" in resp.headers

    def test_cookie_is_not_rewritten_within_the_interval(self, monkeypatch):
        app = _app()
        now = [1_000_000.0]
        monkeypatch.setattr(_session.time, "time", lambda: now[0])
        self._login(app)

        now[0] += _session.SESSION_RENEW_INTERVAL - 1
        resp = app.client.get("/probe")

        assert "set-cookie" not in resp.headers

    def test_anonymous_requests_do_not_set_a_cookie(self):
        resp = _app().client.get("/probe")

        assert "set-cookie" not in resp.headers


class TestLoginPageTemplate:
    def _login_html(self, **kwargs) -> str:
        hx = WebApp(default_page_template=kwargs.pop("default", None))
        configure_user_authentication(
            hx, users=_repo(), secret_key=TEST_SECRET, **kwargs
        )
        return TestClient(hx.create_app()).get("/login").text

    def test_canvas_app_logs_in_on_the_canvas(self):
        html = self._login_html(default=CanvasShell())

        assert 'data-hx-page-template="canvas-shell"' in html
        assert 'data-hx-design="canvas"' in html

    def test_app_shell_app_logs_in_without_navigation(self):
        html = self._login_html(default=AppShell())

        assert 'data-hx-page-template="app-shell"' in html
        assert 'data-hx-main-menu="false"' in html

    def test_login_page_template_overrides_the_default(self):
        html = self._login_html(default=AppShell(), login_page_template=CanvasShell())

        assert 'data-hx-page-template="canvas-shell"' in html

    def test_login_boxes_are_cards_with_the_page_title(self):
        html = self._login_html(default=CanvasShell())

        assert '<section class="hx-card">' in html
        assert "<h1>Sign in</h1>" in html
