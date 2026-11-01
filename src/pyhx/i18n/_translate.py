"""Marking and translating texts in the language of the request."""

from string import Formatter
from typing import Any

import htpy as y
from babel.support import LazyProxy

from pyhx.core.primitives.negotiate_locale import negotiate_locale

from ._catalogs import translations


def _fill(translated: str, source: str, values: dict[str, Any]) -> str:
    if not values:
        return translated
    try:
        return translated.format(**values)
    except KeyError, IndexError, ValueError:
        # A translation with other placeholders than its source (the check
        # reports it) must not fail the request.
        return source.format(**values)


def _(message: str, /, **values: Any) -> str:
    """Translate ``message`` into the language of the request.

    The English source text is the key. Named placeholders are filled after
    the translation, so a translation can place them anywhere.

    Parameters
    ----------
    message
        The source text, e.g. ``"Save"`` or ``"Hello {name}"``.
    **values
        Values of the placeholders.

    Returns
    -------
    str
        The translation, or ``message`` if there is none.

    Examples
    --------
    >>> _("Signed in as {name}.", name="Jane")
    'Angemeldet als Jane.'
    """
    return _fill(translations(negotiate_locale()).gettext(message), message, values)


def _n(singular: str, plural: str, n: int, /, **values: Any) -> str:
    """Translate a text with a plural; ``{n}`` is filled with ``n``.

    Each language picks its own plural form (some have more than two).

    Examples
    --------
    >>> _n("{n} case", "{n} cases", 3)
    '3 Fälle'
    """
    translated = translations(negotiate_locale()).ngettext(singular, plural, n)
    return _fill(translated, singular if n == 1 else plural, {"n": n, **values})


def _p(context: str, message: str, /, **values: Any) -> str:
    """Translate ``message`` in a ``context``, for words with several meanings.

    Examples
    --------
    >>> _p("verb", "Open")
    'Öffnen'
    """
    return _fill(
        translations(negotiate_locale()).pgettext(context, message), message, values
    )


def _l(message: str, /, **values: Any) -> LazyProxy:
    """Mark ``message`` for translation when it is used, not when it is defined.

    For texts defined at import time (module constants, class attributes),
    when no request language is known yet. The result behaves like a ``str``
    and is translated each time it is turned into one.
    """
    return LazyProxy(lambda: _(message, **values), enable_cache=False)


def t(message: str, /, **values: y.Node) -> list[y.Node]:
    """Translate ``message`` and fill its placeholders with nodes.

    Like :func:`_`, but a placeholder can be markup: the result is a list of
    nodes to put into an element. The text is escaped by htpy, the values
    are kept as they are.

    Parameters
    ----------
    message
        The source text, e.g. ``"Signed in as {name}."``.
    **values
        Nodes (or strings) for the placeholders.

    Returns
    -------
    list of htpy.Node
        Text parts and values in the order of the translation.

    Examples
    --------
    >>> y.p[t("Signed in as {name}.", name=y.strong["Jane"])]
    """
    translated = translations(negotiate_locale()).gettext(message)
    for template in (translated, message):
        try:
            parts: list[y.Node] = []
            for literal, field, _spec, _conversion in Formatter().parse(template):
                if literal:
                    parts.append(literal)
                if field is not None:
                    parts.append(values[field])
            return parts
        except KeyError, ValueError:
            continue
    return [message]
