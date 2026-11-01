"""Updating and checking translation catalogs (``python -m pyhx.i18n``)."""

from collections.abc import Iterable, Sequence
from pathlib import Path
from string import Formatter

from babel.messages.catalog import Catalog, Message
from babel.messages.extract import extract_from_dir
from babel.messages.pofile import read_po, write_po

from ._catalogs import catalog_path

KEYWORDS = {"_": None, "_n": (1, 2), "_p": ((1, "c"), 2), "_l": None, "t": None}
"""The marking functions and their arguments, as the extractor reads them."""

SOURCE_LANGUAGE = "en"
"""The language of the source texts; it needs no catalog."""


def translated_locales(locales: Iterable[str]) -> list[str]:
    """The locales that need a catalog: all but the source language."""
    return [
        locale
        for locale in locales
        if locale.replace("_", "-").split("-")[0].lower() != SOURCE_LANGUAGE
    ]


def _scanned(directory: str) -> bool:
    """Whether to look into a directory: all but hidden ones and ``__pycache__``.

    Babel's default skips every directory starting with ``_``, which would
    skip the layers of an app (``_01_domain``, ``_02_webapp``).
    """
    name = Path(directory).name
    return not name.startswith(".") and name != "__pycache__"


def extract(package: Path) -> Catalog:
    """Extract the marked texts of all Python files below ``package``."""
    template = Catalog()
    for filename, lineno, message, comments, context in extract_from_dir(
        package,
        method_map=[("**.py", "python")],
        keywords=KEYWORDS,
        directory_filter=_scanned,
        comment_tags=("Translators:",),
        strip_comment_tags=True,
    ):
        template.add(
            message, None, [(filename, lineno)], auto_comments=comments, context=context
        )
    return template


def update(
    package: Path, catalogs: Path, domain: str, locales: Sequence[str]
) -> list[Path]:
    """Bring the catalogs of ``locales`` up to date with the marked texts of ``package``.

    New texts are added untranslated, texts no longer in the code are
    removed, translations of unchanged texts are kept.

    Returns
    -------
    list of Path
        The written catalogs.
    """
    template = extract(package)
    written = []
    for locale in translated_locales(locales):
        path = catalog_path(catalogs, locale, domain)
        if path.is_file():
            with path.open("rb") as file:
                catalog = read_po(file, locale=locale)
            catalog.update(template, no_fuzzy_matching=True)
        else:
            catalog = Catalog(locale=locale, domain=domain)
            catalog.update(template, no_fuzzy_matching=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as file:
            write_po(file, catalog, ignore_obsolete=True, width=0, sort_output=True)
        written.append(path)
    return written


def _fields(text: str) -> set[str]:
    try:
        return {
            field for _, field, _, _ in Formatter().parse(text) if field is not None
        }
    except ValueError:
        return {"<invalid>"}


def _key(message: Message) -> tuple[str, str | None]:
    msgid = message.id[0] if isinstance(message.id, tuple) else message.id
    return str(msgid), message.context


def _placeholder_problem(message: Message) -> bool:
    if isinstance(message.id, tuple):
        source = _fields(message.id[0]) | _fields(message.id[1])
        forms = (
            message.string if isinstance(message.string, tuple) else (message.string,)
        )
        return any(form and not _fields(str(form)) <= source for form in forms)
    return bool(message.string) and _fields(str(message.string)) != _fields(
        str(message.id)
    )


def check(
    package: Path, catalogs: Path, domain: str, locales: Sequence[str]
) -> list[str]:
    """Check the catalogs of ``locales`` against the marked texts of ``package``.

    Returns
    -------
    list of str
        One line per problem: a missing catalog, a text missing in a catalog
        or no longer in the code (run ``update``), an empty or fuzzy entry,
        a translation with other placeholders than its source. Empty if all
        is well.
    """
    template = extract(package)
    expected = {_key(message) for message in template if message.id}
    problems = []
    for locale in translated_locales(locales):
        path = catalog_path(catalogs, locale, domain)
        if not path.is_file():
            problems.append(f"{path}: missing, run `python -m pyhx.i18n update`")
            continue
        with path.open("rb") as file:
            catalog = read_po(file, locale=locale)
        found = {_key(message): message for message in catalog if message.id}
        for key in sorted(expected - found.keys(), key=str):
            problems.append(
                f"{path}: {key[0]!r} is not in the catalog, run `python -m pyhx.i18n update`"
            )
        for key in sorted(found.keys() - expected, key=str):
            problems.append(
                f"{path}: {key[0]!r} is no longer in the code, run `python -m pyhx.i18n update`"
            )
        for key in sorted(found.keys() & expected, key=str):
            message = found[key]
            strings = (
                message.string
                if isinstance(message.string, tuple)
                else (message.string,)
            )
            if not all(strings):
                problems.append(f"{path}: {key[0]!r} is not translated")
            elif message.fuzzy:
                problems.append(f"{path}: {key[0]!r} is fuzzy")
            elif _placeholder_problem(message):
                problems.append(
                    f"{path}: {key[0]!r} has other placeholders than its source"
                )
    return problems
