import htpy as y
import pytest
from commons.users import RegisteredUser, SQLUsersRepository
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import pyhx.components as c
from pyhx.addons.user_authentication import (
    configure_user_session,
    login_user,
    logout_user,
)
from pyhx.addons.user_authentication._session import safe_next
from pyhx.core.primitives import negotiate_locale
from pyhx.core.request_context import RequestContext
from pyhx.core.webapp import WebApp

from .test_email_login import _app as _email_app
from .test_email_login import _request_link

SECRET = "x" * 32


def _repo() -> SQLUsersRepository:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repo = SQLUsersRepository(engine)
    repo.upsert_user(
        RegisteredUser.create("jane", None, "Jane Doe", email="jane@example.com")
    )
    repo.upsert_user(
        RegisteredUser.create(
            "marco", None, "Marco Rossi", email="marco@example.com", locale="it"
        )
    )
    return repo


class Browser:
    def __init__(self, hx: WebApp) -> None:
        self.client = TestClient(hx.create_app(), follow_redirects=False)

    def locale(self) -> str:
        return self.client.get("/probe").text

    def switch(self, locale: str, next_: str = "/probe", **headers: str):
        return self.client.post(
            "/_pyhx/locale", data={"locale": locale, "next": next_}, headers=headers
        )


def _app(repo: SQLUsersRepository) -> WebApp:
    hx = WebApp()

    @hx.fragment.get("/probe")
    async def probe() -> y.Node:
        return y.span[negotiate_locale()]

    @hx.fragment.post("/login/{username}")
    async def login(username: str) -> y.Node:
        login_user(RequestContext.get_request(), repo.get_user_by_username(username))
        return y.span["in"]

    @hx.fragment.post("/logout")
    async def logout() -> y.Node:
        logout_user(RequestContext.get_request())
        return y.span["out"]

    @hx.fragment.get("/switcher")
    async def switcher() -> y.Node:
        return c.locale_switcher()

    configure_user_session(hx, users=repo, secret_key=SECRET, https_only=False)
    return hx


@pytest.fixture
def repo():
    return _repo()


@pytest.fixture
def hx(repo):
    return _app(repo)


class TestSwitching:
    def test_anonymous_switch_is_stored_in_the_session_only(self, hx, repo):
        browser = Browser(hx)

        response = browser.switch("de")

        assert response.status_code == 303 and response.headers["location"] == "/probe"
        assert "de" in browser.locale()
        assert repo.get_user_by_username("jane").locale is None
        assert "en" in Browser(hx).locale()  # another browser keeps the default

    def test_signed_in_switch_is_stored_on_the_user_and_holds_after_signing_in_again(
        self, hx, repo
    ):
        browser = Browser(hx)
        browser.client.post("/login/jane")

        browser.switch("fr")

        assert repo.get_user_by_username("jane").locale == "fr"
        fresh = Browser(hx)
        assert "en" in fresh.locale()
        fresh.client.post("/login/jane")
        assert "fr" in fresh.locale()

    def test_stored_user_language_applies_without_choosing(self, hx):
        browser = Browser(hx)
        browser.client.post("/login/marco")

        assert "it" in browser.locale()

    def test_session_beats_the_user(self, hx, repo):
        browser = Browser(hx)
        browser.switch("de")
        browser.client.post("/login/marco")

        assert "de" in browser.locale()
        assert repo.get_user_by_username("marco").locale == "it"

    def test_sign_in_and_out_keep_the_session_language(self, hx):
        browser = Browser(hx)
        browser.switch("fr")
        browser.client.post("/login/jane")
        assert "fr" in browser.locale()
        browser.client.post("/logout")
        assert "fr" in browser.locale()

    def test_htmx_request_reloads_the_page(self, hx):
        response = Browser(hx).switch("it", **{"HX-Request": "true"})

        assert response.status_code == 200 and response.headers["HX-Refresh"] == "true"

    @pytest.mark.parametrize(
        "next_", ["https://evil.example/x", "//evil.example", "/\\evil.example", ""]
    )
    def test_foreign_or_missing_next_goes_home(self, hx, next_):
        assert Browser(hx).switch("de", next_=next_).headers["location"] == "/"

    def test_unknown_language_is_rejected_and_nothing_stored(self, hx):
        browser = Browser(hx)

        assert browser.switch("es").status_code == 400
        assert "en" in browser.locale()


class TestSwitcher:
    def test_lists_languages_by_their_own_name_and_marks_the_current(self, hx):
        browser = Browser(hx)
        browser.switch("de")

        html = browser.client.get(
            "/switcher", headers={"HX-Current-URL": "http://test/cases?page=2"}
        ).text

        for name in ("English", "Deutsch", "Italiano", "Français"):
            assert name in html
        assert 'value="de" lang="de"' in html or 'lang="de"' in html
        assert 'name="next" value="/cases?page=2"' in html
        assert html.count('aria-pressed="true"') == 1
        assert 'aria-label="Sprache"' in html or 'aria-label="Language"' in html

    def test_renders_nothing_without_a_session(self):
        hx = WebApp()

        @hx.fragment.get("/switcher")
        async def switcher() -> y.Node:
            return y.div[c.locale_switcher()]

        assert TestClient(hx.create_app()).get("/switcher").text.endswith("<div></div>")


class TestSafeNext:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("/cases", "/cases"),
            ("/a?b=c", "/a?b=c"),
            ("//x", None),
            ("/\\x", None),
            ("http://x", None),
            (None, None),
        ],
    )
    def test_only_same_origin_paths(self, value, expected):
        assert safe_next(value) == expected


class TestLoginMailLanguage:
    def test_session_language_of_the_login_page(self):
        app = _email_app()
        app.client.post("/_pyhx/locale", data={"locale": "fr", "next": "/login"})

        _request_link(app)

        assert app.sender.last.locale == "fr"

    def test_browser_language_without_session_or_user_language(self):
        app = _email_app()
        app.client.headers["Accept-Language"] = "it-CH, de;q=0.5"

        _request_link(app)

        assert app.sender.last.locale == "it"

    def test_default_without_anything(self):
        app = _email_app()

        _request_link(app)

        assert app.sender.last.locale == "en"

    def test_stored_language_of_the_user_without_a_session_language(self):
        from commons.users.login_tokens import (
            InMemoryLoginTokenStore,
            LoginTokenSettings,
        )

        from pyhx.addons.user_authentication import (
            EmailTokenLogin,
            configure_user_authentication,
        )

        from .test_email_login import EMAIL_SUBMIT_URL, CollectingSender

        sender = CollectingSender()
        hx = WebApp()
        login = EmailTokenLogin(
            store=InMemoryLoginTokenStore(),
            sender=sender,
            settings=LoginTokenSettings(),
            base_url="https://x.test",
        )
        configure_user_authentication(
            hx,
            users=_repo(),
            login_methods=[login],
            secret_key=SECRET,
            https_only=False,
        )
        client = TestClient(hx.create_app(), follow_redirects=False)
        client.headers["Accept-Language"] = "de"

        client.post(EMAIL_SUBMIT_URL, data={"email": "Marco@Example.com", "next": ""})

        assert sender.last.locale == "it"
