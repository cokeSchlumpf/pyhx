import re
from importlib.resources import files

import htpy as y
import pytest
from fastapi.testclient import TestClient

from pyhx.core.primitives.negotiate_locale import LocaleSettings
from pyhx.core.webapp import WebApp
from pyhx.page_templates import AppShell


@pytest.fixture
def two_languages(monkeypatch):
    settings = LocaleSettings(supported_locales=["en", "de"])
    monkeypatch.setattr(LocaleSettings, "read", staticmethod(lambda: settings))


def _page(language: str) -> str:
    hx = WebApp(default_page_template=AppShell(mode="app"))

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.p["home"]

    hx.navigation.set({"": [hx.nav_item(home, icon="home")]})
    client = TestClient(hx.create_app())
    return client.get("/", headers={"Accept-Language": language}).text


@pytest.mark.usefixtures("two_languages")
class TestAppShellNavigation:
    @pytest.mark.parametrize("language", ["en", "de"])
    def test_navs_carry_fixed_classes_in_every_language(self, language):
        page = _page(language)

        assert re.search(r'<nav class="hx-main-nav" aria-label="[^"]+"', page)
        assert re.search(r'<nav class="hx-user-nav" aria-label="[^"]+"', page)

    def test_accessible_names_are_translated(self):
        page = _page("de")

        assert 'aria-label="Hauptnavigation"' in page
        assert 'aria-label="Benutzermenü"' in page

    def test_styles_do_not_select_on_translated_names(self):
        css = (files("pyhx") / "static/css/page-templates/app-shell.css").read_text(
            encoding="utf-8"
        )

        assert "aria-label" not in css
