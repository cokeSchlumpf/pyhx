"""Loading the translation catalogs of the app and of pyhx."""

from functools import lru_cache
from gettext import NullTranslations
from io import BytesIO
from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from babel.support import Translations
from commons.path_operators import get_project_root_dir

PYHX_LOCALE_DIR = Path(__file__).parent.parent / "locale"
"""Directory of pyhx's own translations (domain ``pyhx``)."""

PYHX_DOMAIN = "pyhx"
APP_DOMAIN = "messages"


def app_locale_dir() -> Path:
    """The app's catalog directory: ``WebApp.locale_dir``, else ``<project root>/locale``."""
    from pyhx.core.webapp import WebApp

    try:
        return WebApp.get().locale_dir
    except LookupError:
        return get_project_root_dir() / "locale"


def catalog_path(directory: Path, locale: str, domain: str) -> Path:
    """The path of a catalog: ``<directory>/<locale>/LC_MESSAGES/<domain>.po``."""
    return directory / locale / "LC_MESSAGES" / f"{domain}.po"


def _load(path: Path, locale: str) -> NullTranslations | None:
    """Read a ``.po`` file into translations; fuzzy and empty entries are left out."""
    if not path.is_file():
        return None
    with path.open("rb") as file:
        catalog = read_po(file, locale=locale)
    buffer = BytesIO()
    write_mo(buffer, catalog, use_fuzzy=False)
    buffer.seek(0)
    return Translations(fp=buffer)


@lru_cache(maxsize=64)
def _translations(locale: str, app_dir: Path, pyhx_dir: Path) -> NullTranslations:
    app = _load(catalog_path(app_dir, locale, APP_DOMAIN), locale)
    pyhx = _load(catalog_path(pyhx_dir, locale, PYHX_DOMAIN), locale)
    if app is not None and pyhx is not None:
        app.add_fallback(pyhx)
    return app or pyhx or NullTranslations()


def translations(locale: str) -> NullTranslations:
    """The translations for ``locale``: the app's catalog, falling back to pyhx's.

    Catalogs are read once per process and language; an entry missing in
    both, or a missing catalog, falls back to the source text.
    """
    return _translations(locale, app_locale_dir(), PYHX_LOCALE_DIR)


def clear_cache() -> None:
    """Forget loaded catalogs (e.g. in tests that write catalogs)."""
    _translations.cache_clear()
