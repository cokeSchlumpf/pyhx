from urllib.parse import urlsplit

import htpy as y
from babel import Locale

from pyhx.core import component
from pyhx.core.primitives.negotiate_locale import (
    LOCALE_SWITCH_PATH,
    LocaleSettings,
    negotiate_locale,
)
from pyhx.core.request_context import RequestContext
from pyhx.i18n import _

from .button import button
from .button_group import button_group


def _own_name(locale: str) -> str:
    """The name of a language in itself, capitalized, e.g. ``"Français"``."""
    name = (
        Locale.parse(locale.replace("-", "_")).get_display_name(
            locale.replace("-", "_")
        )
        or locale
    )
    return name[:1].upper() + name[1:]


def _current_path() -> str:
    """The page to return to: the page a fragment was loaded into, else the requested one."""
    request = RequestContext.get_request()
    url = request.headers.get("hx-current-url")
    if url:
        parts = urlsplit(url)
        return parts.path + (f"?{parts.query}" if parts.query else "")
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


@component
def locale_switcher(**kwargs) -> y.Node:
    """Buttons to switch between the languages the app offers.

    Each offered language (``[app.pyhx.core] supported_locales``) is shown by
    its own name ("Deutsch", "Français"), the current one is highlighted.
    Choosing one posts to ``/_pyhx/locale``, which stores the language in the
    session and, for a signed-in registered user, on the user, then reloads
    the page. Works without JavaScript as a plain form.

    The endpoint is registered by the user authentication addon
    (``configure_user_authentication``); without a session the switcher
    renders nothing.

    Examples
    --------
    >>> c.locale_switcher()

    Parameters
    ----------
    **kwargs
        Forwarded to the ``<form>`` (e.g. ``class_=``).
    """
    try:
        request = RequestContext.get_request()
    except LookupError, AssertionError:
        return y.fragment[()]
    if "session" not in request.scope:
        return y.fragment[()]

    current = negotiate_locale()
    return y.form(
        ".hx-locale-switcher",
        method="post",
        action=LOCALE_SWITCH_PATH,
        hx_post=LOCALE_SWITCH_PATH,
        aria_label=_("Language"),
        **kwargs,
    )[
        y.input(type="hidden", name="next", value=_current_path()),
        button_group(
            *(
                button(
                    _own_name(locale),
                    type="submit",
                    name="locale",
                    value=locale,
                    lang=locale,
                    size="sm",
                    variant="outline" if locale == current else "ghost",
                    aria_pressed="true" if locale == current else "false",
                )
                for locale in LocaleSettings.read().supported_locales
            )
        ),
    ]
