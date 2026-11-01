import htpy as y
import pytest
from commons.users import SQLUsersRepository
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from pyhx.addons.user_authentication import configure_user_session
from pyhx.core.primitives.negotiate_locale import LocaleSettings
from pyhx.core.webapp import WebApp
from pyhx.i18n import _l
from pyhx.page_templates import (
    AppShell,
    CanvasShell,
    LanguageSetting,
    SettingsLink,
    SettingsLinks,
)

SECRET = "x" * 32


def _client(template, *, session: bool = True) -> TestClient:
    hx = WebApp(default_page_template=template)

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.p["home"]

    if session:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        configure_user_session(
            hx, users=SQLUsersRepository(engine), secret_key=SECRET, https_only=False
        )
    return TestClient(hx.create_app(), follow_redirects=False)


@pytest.fixture
def four_languages(monkeypatch):
    settings = LocaleSettings(supported_locales=["en", "de", "it", "fr"])
    monkeypatch.setattr(LocaleSettings, "read", staticmethod(lambda: settings))


TEMPLATES = [
    pytest.param(
        lambda **kw: AppShell(mode="app", main_navigation=False, **kw), id="AppShell"
    ),
    pytest.param(lambda **kw: CanvasShell(**kw), id="CanvasShell"),
]


@pytest.mark.usefixtures("four_languages")
class TestSettingsMenu:
    @pytest.mark.parametrize("make", TEMPLATES)
    def test_gear_with_the_language_section_by_default(self, make):
        page = _client(make()).get("/", headers={"Accept-Language": "de"}).text

        assert '<details class="hx-settings-menu">' in page
        assert 'aria-label="Einstellungen"' in page
        assert '<h2 id="hx-settings-language">Sprache</h2><span>Deutsch</span>' in page
        assert 'action="/_pyhx/locale"' in page and 'name="next" value="/"' in page
        assert 'hx-trigger="change"' in page
        assert "hx-segment-control--md" in page
        assert 'aria-labelledby="hx-settings-language"' in page
        for code in ("en", "de", "it", "fr"):
            assert f'name="locale" value="{code}"' in page
        assert page.count(" checked") == 1
        assert 'value="de" checked><span>DE</span>' in page

    @pytest.mark.parametrize("make", TEMPLATES)
    def test_no_gear_without_settings(self, make):
        assert "hx-settings-menu" not in _client(make(settings=())).get("/").text

    @pytest.mark.parametrize("make", TEMPLATES)
    def test_no_gear_without_a_session(self, make):
        assert "hx-settings-menu" not in _client(make(), session=False).get("/").text

    @pytest.mark.parametrize("make", TEMPLATES)
    def test_entries_are_sections_and_empty_ones_are_left_out(self, make):
        def theme() -> y.Node:
            return y.section(".hx-settings-menu__section")[y.h2["Theme"]]

        def nothing() -> y.Node:
            return None

        page = _client(make(settings=[LanguageSetting(), nothing, theme])).get("/").text

        assert page.index("hx-settings-language") < page.index("<h2>Theme</h2>")

    @pytest.mark.parametrize("make", TEMPLATES)
    def test_links_above_the_language(self, make):
        links = SettingsLinks(
            SettingsLink(_l("Profile"), "/profile", icon="user"),
            SettingsLink("Sign out", "/logout", icon="log-out"),
        )

        page = _client(make(settings=[links, LanguageSetting()])).get("/").text

        start = page.index('<ul class="hx-settings-menu__links">')
        assert (
            start
            < page.index('href="/profile"')
            < page.index('href="/logout"')
            < page.index("hx-settings-language")
        )
        assert "<span>Profile</span>" in page and "<span>Sign out</span>" in page

    def test_no_links_no_section(self):
        assert SettingsLinks()() is None

    def test_the_canvas_menu_is_outside_the_clipped_header_content(self):
        page = _client(CanvasShell(header_content=y.span["Jane"])).get("/").text

        content = page.index('class="hx-canvas-shell__header-content"')
        assert (
            content
            < page.index("<span>Jane</span>")
            < page.index('<details class="hx-settings-menu">')
        )
        assert page.index('class="hx-canvas-shell__header-end"') < content


def test_no_gear_with_one_language(monkeypatch):
    settings = LocaleSettings(supported_locales=["en"])
    monkeypatch.setattr(LocaleSettings, "read", staticmethod(lambda: settings))

    assert "hx-settings-menu" not in _client(CanvasShell()).get("/").text
