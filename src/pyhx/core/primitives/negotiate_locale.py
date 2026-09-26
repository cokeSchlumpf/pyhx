"""Locale negotiation off the current request's ``Accept-Language`` header.

Reusable building block for any locale-aware formatter (dates, numbers,
currencies, plurals). The supported-language set and default come from
:class:`LocaleSettings` so deployments can override via TOML or env.
"""

from typing import Any

from babel import negotiate_locale as _babel_negotiate
from commons.settings import read_settings_object

from ..request_context import RequestContext


class LocaleSettings:
    """Locale negotiation defaults for pyhx.

    Read from the merged settings tree at ``app.pyhx.core.*`` — same shape
    as :class:`UserSessionSettings`. Defaults to the four languages pyhx
    ships UI strings for.

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
    def read() -> "LocaleSettings":
        return read_settings_object("pyhx.core", LocaleSettings)


def negotiate_locale(*, fallback: str | None = None) -> str:
    """Pick the best supported locale for the current request.

    Resolution at call time:

    1. Read :class:`LocaleSettings` (supported set + default).
    2. If no request is in context (background task, render outside a
       request scope), return ``fallback`` if given else the configured
       default.
    3. Parse ``Accept-Language`` and run babel's quality-weighted
       negotiation against the supported set; on no match, return
       ``fallback`` if given else the configured default.

    Never raises.
    """
    settings = LocaleSettings.read()
    default = fallback if fallback is not None else settings.default_locale
    try:
        ctx = RequestContext.get()
    except LookupError:
        return default
    if ctx.request is None:
        return default
    header = ctx.request.headers.get("accept-language", "")
    preferred = [tag.split(";")[0].strip() for tag in header.split(",") if tag.strip()]
    return _babel_negotiate(preferred, list(settings.supported_locales)) or default
