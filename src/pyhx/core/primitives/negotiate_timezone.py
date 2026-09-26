"""Timezone negotiation off a client-set cookie.

Browsers send an ``Accept-Language`` header but have *no* equivalent for the
timezone — there is no ``Accept-Timezone``. So unlike :mod:`negotiate_locale`,
the server can never learn the user's IANA zone from the request alone. The
zone is detected client-side via ``Intl.DateTimeFormat().resolvedOptions()``
and written to the ``hx_tz`` cookie (see the inline snippet in
:class:`pyhx.core.templates.skeleton.Skeleton`), which then rides along with
every subsequent request exactly like the language headers do.

The configured default (``UTC`` unless overridden) is used on the very first
request — before any page has had a chance to set the cookie — and whenever
the cookie is missing or holds an unknown zone.
"""

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from commons.settings import read_settings_object

from ..request_context import RequestContext

TIMEZONE_COOKIE = "hx_tz"
"""Cookie name the client-side snippet writes the detected IANA zone into."""


class TimezoneSettings:
    """Timezone default for pyhx.

    Read from the merged settings tree at ``app.pyhx.core.*`` — the same
    namespace as :class:`~pyhx.core.primitives.negotiate_locale.LocaleSettings`.
    Defaults to ``UTC`` so date/time rendering is deterministic until a
    deployment opts into a different house zone.

    TOML::

        [app.pyhx.core]
        default_timezone = "Europe/Zurich"

    Env var override follows the standard pattern
    (``APP__PYHX__CORE__DEFAULT_TIMEZONE``).
    """

    def __init__(
        self,
        default_timezone: str = "UTC",
        **_kwargs: Any,
    ) -> None:
        self.default_timezone = default_timezone

    @staticmethod
    def read() -> "TimezoneSettings":
        return read_settings_object("pyhx.core", TimezoneSettings)


def _is_valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return False


def negotiate_timezone(*, fallback: str | None = None) -> str:
    """Pick the IANA timezone for the current request.

    Resolution at call time:

    1. Read :class:`TimezoneSettings` (the configured default).
    2. If no request is in context (background task, render outside a
       request scope), return ``fallback`` if given else the configured
       default.
    3. Read the ``hx_tz`` cookie. If present and a valid IANA zone, use it.
    4. Otherwise return ``fallback`` if given else the configured default.

    Never raises — an unknown or malformed cookie value falls through to the
    default rather than propagating a ``ZoneInfo`` lookup error.
    """
    settings = TimezoneSettings.read()
    default = fallback if fallback is not None else settings.default_timezone
    try:
        ctx = RequestContext.get()
    except LookupError:
        return default
    if ctx.request is None:
        return default
    cookie = ctx.request.cookies.get(TIMEZONE_COOKIE)
    if cookie and _is_valid_timezone(cookie):
        return cookie
    return default
