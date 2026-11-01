"""Multilingual apps: the language of a request, translated texts, formatting.

Mark texts with ``_`` (plain), ``_n`` (plural), ``_p`` (with a context),
``_l`` (translated when used, for texts defined at import time) and ``t``
(placeholders filled with markup). The English source text is the key;
placeholders are named (``{name}``) and filled after the translation.

Texts are looked up in the app's catalog
(``<project root>/locale/<lang>/LC_MESSAGES/messages.po``, or
``WebApp(locale_dir=…)``), then in pyhx's catalog (de, it, fr), then the
source text is used. The ``format_*`` helpers format numbers, dates and
times in the language and timezone of the request. ``python -m pyhx.i18n update`` extracts the marked texts
into the catalogs, ``python -m pyhx.i18n check`` finds missing translations.

The language of a request comes from the session, the signed-in user, the
browser and the app's default, in this order (see
:mod:`pyhx.core.primitives.negotiate_locale`); the offered languages are set
in ``[app.pyhx.core]``. See the guide "Multilingual apps".

Examples
--------
>>> import htpy as y
>>> from pyhx.i18n import _, _n, t
>>> y.h1[_("Cases")]
>>> y.p[_n("{n} open case", "{n} open cases", count)]
>>> y.p[t("Signed in as {name}.", name=y.strong[user.display_name])]
"""

from pyhx.core.primitives.lazy_text import LazyText, Text
from pyhx.core.primitives.negotiate_locale import (
    LOCALE_SWITCH_PATH,
    LocaleSettings,
    negotiate_locale,
    resolve_locale,
    use_locale,
)

from ._format import (
    format_currency,
    format_date,
    format_datetime,
    format_number,
    format_percent,
    format_relative_time,
    format_time,
)
from ._switch import LocaleOption, LocaleSwitch, locale_switch
from ._translate import _, _l, _n, _p, t

__all__ = [
    "LOCALE_SWITCH_PATH",
    "LazyText",
    "LocaleOption",
    "LocaleSettings",
    "LocaleSwitch",
    "Text",
    "_",
    "_l",
    "_n",
    "_p",
    "format_currency",
    "format_date",
    "format_datetime",
    "format_number",
    "format_percent",
    "format_relative_time",
    "format_time",
    "locale_switch",
    "negotiate_locale",
    "resolve_locale",
    "t",
    "use_locale",
]
