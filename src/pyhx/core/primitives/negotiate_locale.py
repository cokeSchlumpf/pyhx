"""The language of the current request.

The language is resolved once per request, from the first of these that
names a language the app offers:

1. the language stored in the session (``session["pyhx.locale"]``, written by
   the language switcher of the user authentication addon),
2. the language of the signed-in user (``user.locale``, e.g.
   ``RegisteredUser.locale`` of commons),
3. the browser languages of ``Accept-Language``, by their weight,
4. the app's default.

The offered languages and the default come from :class:`LocaleSettings`. All
texts (:mod:`pyhx.i18n`) and all locale-aware formatting (data tables, the
format helpers of :mod:`pyhx.i18n`) use this one language.
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from commons.settings import read_settings_object

from ..request_context import RequestContext

SESSION_LOCALE_KEY = "pyhx.locale"
"""Session key of the language a visitor chose."""

LOCALE_SWITCH_PATH = "/_pyhx/locale"
"""Endpoint of the language switcher (registered by the user authentication addon)."""


class LocaleSettings:
    """The languages an app offers and its default.

    Read from the merged settings tree at ``app.pyhx.core.*``. pyhx ships
    translations of its own texts for German, Italian and French; English is
    the source language. An app offering another language adds it here and
    translates pyhx's texts in its own catalog.

    TOML::

        [app.pyhx.core]
        supported_locales = ["en", "de", "it", "fr"]
        default_locale = "en"

    Env var overrides follow the standard pattern
    (``APP__PYHX__CORE__SUPPORTED_LOCALES``, ``APP__PYHX__CORE__DEFAULT_LOCALE``).
    """

    def __init__(
        self,
        supported_locales: list[str] | None = None,
        default_locale: str = "en",
        **_kwargs: Any,
    ) -> None:
        self.supported_locales: tuple[str, ...] = tuple(
            supported_locales
            if supported_locales is not None
            else ["en", "de", "it", "fr"]
        )
        self.default_locale = default_locale

    @staticmethod
    def read() -> LocaleSettings:
        return read_settings_object("pyhx.core", LocaleSettings)


_override: ContextVar[str | None] = ContextVar("pyhx.locale_override", default=None)


def match_locale(candidate: str | None, supported: Sequence[str]) -> str | None:
    """Return the offered language ``candidate`` names, or ``None``.

    Matching ignores case and treats ``_`` like ``-``; a regional variant
    falls back to its language (``"de-CH"`` matches ``"de"``).

    Parameters
    ----------
    candidate
        A language tag, e.g. from the session or a header.
    supported
        The offered languages.

    Returns
    -------
    str or None
        The matching entry of ``supported``, as spelled there.
    """
    if not candidate:
        return None
    wanted = candidate.strip().replace("_", "-").lower()
    by_key = {tag.replace("_", "-").lower(): tag for tag in supported}
    if wanted in by_key:
        return by_key[wanted]
    return by_key.get(wanted.split("-")[0])


def parse_accept_language(header: str) -> list[str]:
    """Return the language tags of an ``Accept-Language`` header, best first.

    Entries are ordered by their ``q`` weight (default ``1``), keeping the
    header order among equal weights; ``*`` and entries with ``q=0`` are
    dropped.

    Parameters
    ----------
    header
        The header value, e.g. ``"de-CH,de;q=0.9,en;q=0.8"``.

    Returns
    -------
    list of str
        The tags, e.g. ``["de-CH", "de", "en"]``.
    """
    weighted: list[tuple[float, int, str]] = []
    for index, entry in enumerate(header.split(",")):
        tag, _, params = entry.strip().partition(";")
        tag = tag.strip()
        if not tag or tag == "*":
            continue
        weight = 1.0
        for param in params.split(";"):
            name, _, value = param.strip().partition("=")
            if name.strip() == "q":
                try:
                    weight = float(value)
                except ValueError:
                    weight = 0.0
        if weight > 0:
            weighted.append((-weight, index, tag))
    return [tag for _, _, tag in sorted(weighted)]


def resolve_locale(
    ctx: RequestContext | None = None, *, user: Any = None
) -> str | None:
    """Resolve the language of a request, without the default.

    Runs the order of this module (session, user, ``Accept-Language``) and
    returns the first offered language, or ``None`` if none matches.

    Parameters
    ----------
    ctx
        The request context; defaults to the current one. Without a request,
        only ``user`` is considered.
    user
        The user whose language is considered in step 2, instead of
        ``ctx.user`` (e.g. the user who requested a login mail).

    Returns
    -------
    str or None
        The language, or ``None`` if nothing matched.
    """
    supported = LocaleSettings.read().supported_locales
    if ctx is None:
        try:
            ctx = RequestContext.get()
        except LookupError:
            ctx = None

    connection = None if ctx is None else ctx.request
    session = None if connection is None else connection.scope.get("session")
    candidates: list[str | None] = [
        session.get(SESSION_LOCALE_KEY) if session else None
    ]
    candidates.append(
        getattr(
            user if user is not None else (ctx.user if ctx else None), "locale", None
        )
    )
    if connection is not None:
        candidates.extend(
            parse_accept_language(connection.headers.get("accept-language", ""))
        )

    for candidate in candidates:
        if (matched := match_locale(candidate, supported)) is not None:
            return matched
    return None


@contextmanager
def use_locale(locale: str) -> Iterator[None]:
    """Use ``locale`` for all texts and formatting inside the block.

    For code outside a request (mails, jobs, tests) or to render one part of
    a page in another language. A language the app doesn't offer falls back
    to its default.

    Parameters
    ----------
    locale
        The language, e.g. ``"de"``.

    Examples
    --------
    >>> with use_locale("de"):
    ...     subject = _("Your sign-in code")
    """
    settings = LocaleSettings.read()
    token = _override.set(
        match_locale(locale, settings.supported_locales) or settings.default_locale
    )
    try:
        yield
    finally:
        _override.reset(token)


def negotiate_locale(*, fallback: str | None = None) -> str:
    """Return the language of the current request.

    The language set with :func:`use_locale` wins; inside a request it is the
    language resolved once per request (see the module docstring); if nothing
    matches or there is no request, ``fallback`` if given, else the default.

    Never raises.
    """
    if (override := _override.get()) is not None:
        return override
    try:
        ctx = RequestContext.get()
    except LookupError:
        ctx = None
    resolved = ctx.resolved_locale() if ctx is not None else None
    if resolved is not None:
        return resolved
    return fallback if fallback is not None else LocaleSettings.read().default_locale
