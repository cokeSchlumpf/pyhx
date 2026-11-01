from pathlib import Path

import htpy as y
import pytest
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

from pyhx.core.webapp import WebApp
from pyhx.i18n import _, _l, _n, _p, t, use_locale
from pyhx.i18n import _catalogs


def write_catalog(directory: Path, locale: str, domain: str, entries: dict) -> None:
    """Write a catalog; keys are msgids, ``(singular, plural)`` or ``(context, msgid)`` with a ``ctx:`` prefix."""
    catalog = Catalog(locale=locale)
    for key, value in entries.items():
        if isinstance(key, tuple) and key[0].startswith("ctx:"):
            catalog.add(key[1], value, context=key[0][4:])
        else:
            catalog.add(key, value, flags=["fuzzy"] if value == "FUZZY" else ())
    path = _catalogs.catalog_path(directory, locale, domain)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        write_po(file, catalog)


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    app_dir, pyhx_dir = tmp_path / "app", tmp_path / "pyhx"
    monkeypatch.setattr(_catalogs, "PYHX_LOCALE_DIR", pyhx_dir)
    webapp = WebApp(locale_dir=app_dir)
    _catalogs.clear_cache()
    yield app_dir, pyhx_dir
    webapp.close()
    _catalogs.clear_cache()


class TestLookup:
    def test_app_beats_pyhx_beats_source(self, dirs):
        app_dir, pyhx_dir = dirs
        write_catalog(
            app_dir, "de", "messages", {"Save": "Übernehmen", "Cases": "Fälle"}
        )
        write_catalog(
            pyhx_dir, "de", "pyhx", {"Save": "Speichern", "Cancel": "Abbrechen"}
        )

        with use_locale("de"):
            assert [_("Save"), _("Cancel"), _("Cases"), _("Unknown")] == [
                "Übernehmen",
                "Abbrechen",
                "Fälle",
                "Unknown",
            ]

    def test_without_an_app_catalog_pyhx_applies(self, dirs):
        _app_dir, pyhx_dir = dirs
        write_catalog(pyhx_dir, "fr", "pyhx", {"Cancel": "Annuler"})

        with use_locale("fr"):
            assert _("Cancel") == "Annuler"

    def test_missing_catalogs_fall_back_to_the_source(self, dirs):
        with use_locale("it"):
            assert _("Save") == "Save"

    def test_fuzzy_entries_are_not_used(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(app_dir, "de", "messages", {"Save": "FUZZY"})

        with use_locale("de"):
            assert _("Save") == "Save"

    def test_english_needs_no_catalog(self, dirs):
        with use_locale("en"):
            assert _("Save") == "Save"


class TestPlaceholders:
    def test_translation_reorders_placeholders(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(
            app_dir,
            "de",
            "messages",
            {
                "Case {case} was closed by {user}.": "{user} hat den Fall {case} geschlossen."
            },
        )

        with use_locale("de"):
            assert (
                _("Case {case} was closed by {user}.", case="A-1", user="Jane")
                == "Jane hat den Fall A-1 geschlossen."
            )

    def test_a_translation_with_wrong_placeholders_falls_back_to_the_source(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(app_dir, "de", "messages", {"Hello {name}": "Hallo {nmae}"})

        with use_locale("de"):
            assert _("Hello {name}", name="Jane") == "Hello Jane"

    def test_t_fills_placeholders_with_nodes_and_escapes_text(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(
            app_dir,
            "de",
            "messages",
            {"Signed in as {name}.": "Angemeldet <als> {name}."},
        )

        with use_locale("de"):
            html = str(y.p[t("Signed in as {name}.", name=y.strong["<Jane>"])])

        assert html == "<p>Angemeldet &lt;als&gt; <strong>&lt;Jane&gt;</strong>.</p>"

    def test_t_without_translation_uses_the_source(self, dirs):
        assert (
            str(y.p[t("Signed in as {name}.", name=y.strong["Jane"])])
            == "<p>Signed in as <strong>Jane</strong>.</p>"
        )


class TestPluralsAndContexts:
    def test_plural_forms_per_language(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(
            app_dir,
            "de",
            "messages",
            {("{n} case", "{n} cases"): ("{n} Fall", "{n} Fälle")},
        )
        write_catalog(
            app_dir,
            "fr",
            "messages",
            {("{n} case", "{n} cases"): ("{n} dossier", "{n} dossiers")},
        )

        with use_locale("de"):
            assert [_n("{n} case", "{n} cases", n) for n in (0, 1, 2)] == [
                "0 Fälle",
                "1 Fall",
                "2 Fälle",
            ]
        with use_locale("fr"):
            # French uses the singular for 0.
            assert [_n("{n} case", "{n} cases", n) for n in (0, 1, 2)] == [
                "0 dossier",
                "1 dossier",
                "2 dossiers",
            ]
        with use_locale("en"):
            assert [_n("{n} case", "{n} cases", n) for n in (1, 2)] == [
                "1 case",
                "2 cases",
            ]

    def test_context(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(
            app_dir,
            "de",
            "messages",
            {("ctx:verb", "Open"): "Öffnen", ("ctx:state", "Open"): "Offen"},
        )

        with use_locale("de"):
            assert (_p("verb", "Open"), _p("state", "Open"), _("Open")) == (
                "Öffnen",
                "Offen",
                "Open",
            )


class TestLazy:
    def test_translated_when_used(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(app_dir, "de", "messages", {"Cases": "Fälle"})
        write_catalog(app_dir, "it", "messages", {"Cases": "Casi"})
        label = _l("Cases")

        with use_locale("de"):
            assert str(label) == "Fälle"
        with use_locale("it"):
            assert f"{label}" == "Casi"

    def test_renders_in_htpy_and_page_titles(self, dirs):
        app_dir, _pyhx_dir = dirs
        write_catalog(app_dir, "de", "messages", {"Cases & more": "Fälle & mehr"})
        label = _l("Cases & more")

        with use_locale("de"):
            assert str(y.h1[label]) == "<h1>Fälle &amp; mehr</h1>"
            assert f"{label} | App" == "Fälle & mehr | App"
            assert (
                str(y.a(title=str(label))["x"]) == '<a title="Fälle &amp; mehr">x</a>'
            )


class TestPyhxCatalogs:
    def test_ship_with_the_package(self):
        from pyhx.i18n._catalogs import PYHX_LOCALE_DIR, clear_cache

        clear_cache()
        for locale, cancel in (
            ("de", "Abbrechen"),
            ("it", "Annulla"),
            ("fr", "Annuler"),
        ):
            assert (PYHX_LOCALE_DIR / locale / "LC_MESSAGES" / "pyhx.po").is_file()
            with use_locale(locale):
                assert _("Cancel") == cancel
