"""Update and check translation catalogs.

Usage::

    python -m pyhx.i18n update   # extract the marked texts into the catalogs
    python -m pyhx.i18n check    # fail on missing, empty, fuzzy or broken translations

The defaults fit an app (``src/app``, ``locale/``, domain ``messages``, the
languages of ``[app.pyhx.core] supported_locales`` except English); pyhx
itself runs ``check --package src/pyhx --catalogs src/pyhx/locale --domain pyhx``.
"""

import argparse
import sys
from pathlib import Path

from pyhx.core.primitives.negotiate_locale import LocaleSettings

from ._tooling import check, translated_locales, update


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pyhx.i18n", description=__doc__.split("\n")[0]
    )
    parser.add_argument("command", choices=["update", "check"])
    parser.add_argument(
        "--package",
        type=Path,
        default=Path("src/app"),
        help="code to extract (default: src/app)",
    )
    parser.add_argument(
        "--catalogs",
        type=Path,
        default=Path("locale"),
        help="catalog directory (default: locale)",
    )
    parser.add_argument(
        "--domain", default="messages", help="catalog name (default: messages)"
    )
    parser.add_argument(
        "--locales",
        help="comma-separated languages (default: [app.pyhx.core] supported_locales)",
    )
    args = parser.parse_args(argv)
    locales = (
        args.locales.split(",")
        if args.locales
        else list(LocaleSettings.read().supported_locales)
    )

    if args.command == "update":
        for path in update(args.package, args.catalogs, args.domain, locales):
            print(f"updated {path}")
        return 0

    problems = check(args.package, args.catalogs, args.domain, locales)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{len(problems)} translation problem(s).", file=sys.stderr)
        return 1
    print(
        f"Translations complete for {', '.join(translated_locales(locales)) or 'no language'}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
