from pathlib import Path

import pytest
from babel.messages.pofile import read_po, write_po

from pyhx.i18n.__main__ import main
from pyhx.i18n._catalogs import catalog_path
from pyhx.i18n._tooling import check, update

CODE = """
from pyhx.i18n import _, _l, _n, _p, t

TITLE = _l("Cases")

def page(n, name):
    # Translators: the button that stores the form
    return [_("Save"), _n("{n} case", "{n} cases", n), _p("verb", "Open"), t("Hello {name}", name=name)]
"""


@pytest.fixture
def project(tmp_path) -> tuple[Path, Path]:
    package = tmp_path / "src" / "app"
    package.mkdir(parents=True)
    (package / "pages.py").write_text(CODE)
    return package, tmp_path / "locale"


def _translate_all(catalogs: Path, locale: str, values: dict[str, object]) -> None:
    path = catalog_path(catalogs, locale, "messages")
    with path.open("rb") as file:
        catalog = read_po(file, locale=locale)
    for message in catalog:
        key = message.id[0] if isinstance(message.id, tuple) else message.id
        if key in values:
            message.string = values[key]
    with path.open("wb") as file:
        write_po(file, catalog)


GERMAN = {
    "Cases": "Fälle",
    "Save": "Speichern",
    "{n} case": ("{n} Fall", "{n} Fälle"),
    "Open": "Öffnen",
    "Hello {name}": "Hallo {name}",
}


class TestUpdate:
    def test_creates_catalogs_for_all_but_the_source_language(self, project):
        package, catalogs = project

        written = update(package, catalogs, "messages", ["en", "de", "fr"])

        assert written == [
            catalog_path(catalogs, "de", "messages"),
            catalog_path(catalogs, "fr", "messages"),
        ]
        with written[0].open("rb") as file:
            catalog = read_po(file, locale="de")
        ids = {
            (m.id if isinstance(m.id, str) else m.id[0], m.context)
            for m in catalog
            if m.id
        }
        assert ids == {
            ("Cases", None),
            ("Save", None),
            ("{n} case", None),
            ("Open", "verb"),
            ("Hello {name}", None),
        }
        assert catalog.get("Save").auto_comments == ["the button that stores the form"]

    def test_keeps_translations_and_drops_removed_texts(self, project):
        package, catalogs = project
        update(package, catalogs, "messages", ["de"])
        _translate_all(catalogs, "de", GERMAN)
        (package / "pages.py").write_text(CODE.replace('_("Save")', '_("Store")'))

        update(package, catalogs, "messages", ["de"])

        with catalog_path(catalogs, "de", "messages").open("rb") as file:
            catalog = read_po(file, locale="de")
        assert catalog.get("Cases").string == "Fälle"
        assert catalog.get("Store").string == ""
        assert catalog.get("Save") is None


class TestCheck:
    def test_passes_when_complete(self, project):
        package, catalogs = project
        update(package, catalogs, "messages", ["de"])
        _translate_all(catalogs, "de", GERMAN)

        assert check(package, catalogs, "messages", ["en", "de"]) == []

    def test_reports_missing_catalog_and_untranslated_entries(self, project):
        package, catalogs = project
        update(package, catalogs, "messages", ["de"])

        problems = check(package, catalogs, "messages", ["de", "it"])

        assert any("it/LC_MESSAGES/messages.po: missing" in p for p in problems)
        assert sum("is not translated" in p for p in problems) == 5

    def test_reports_fuzzy_and_placeholders(self, project):
        package, catalogs = project
        update(package, catalogs, "messages", ["de"])
        _translate_all(catalogs, "de", GERMAN | {"Hello {name}": "Hallo {nmae}"})
        path = catalog_path(catalogs, "de", "messages")
        with path.open("rb") as file:
            catalog = read_po(file, locale="de")
        catalog.get("Save").flags.add("fuzzy")
        with path.open("wb") as file:
            write_po(file, catalog)

        problems = check(package, catalogs, "messages", ["de"])

        assert any("'Save' is fuzzy" in p for p in problems)
        assert any("'Hello {name}' has other placeholders" in p for p in problems)

    def test_reports_outdated_catalogs(self, project):
        package, catalogs = project
        update(package, catalogs, "messages", ["de"])
        _translate_all(catalogs, "de", GERMAN)
        (package / "pages.py").write_text(CODE.replace('_("Save")', '_("Store")'))

        problems = check(package, catalogs, "messages", ["de"])

        assert any("'Store' is not in the catalog" in p for p in problems)
        assert any("'Save' is no longer in the code" in p for p in problems)

    def test_command_line(self, project, capsys):
        package, catalogs = project
        args = [
            "--package",
            str(package),
            "--catalogs",
            str(catalogs),
            "--locales",
            "en,de",
        ]

        assert main(["update", *args]) == 0
        assert main(["check", *args]) == 1
        _translate_all(catalogs, "de", GERMAN)
        assert main(["check", *args]) == 0
        assert "Translations complete for de." in capsys.readouterr().out
