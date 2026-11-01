"""What a language switcher needs, without its markup (headless)."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from babel import Locale

from pyhx.core.primitives.negotiate_locale import (
    LOCALE_SWITCH_PATH,
    LocaleSettings,
    negotiate_locale,
)
from pyhx.core.request_context import RequestContext


@dataclass(frozen=True)
class LocaleOption:
    """One offered language.

    Attributes
    ----------
    locale
        The language tag to post as ``locale``, e.g. ``"de"``.
    name
        Its name in itself, capitalized, e.g. ``"Deutsch"``, ``"Français"``.
    current
        Whether it is the language of the request.
    """

    locale: str
    name: str
    current: bool


@dataclass(frozen=True)
class LocaleSwitch:
    """Everything to render a language switcher in the app's own design.

    Post a form to ``action`` with the fields ``locale`` (the chosen
    language) and ``next`` (the page to return to). The endpoint stores the
    language in the session and, for a signed-in registered user, on the
    user, then reloads the page (``HX-Refresh`` for HTMX requests, else a
    redirect to ``next``).

    Attributes
    ----------
    action
        The endpoint, ``/_pyhx/locale``.
    next
        The page to return to: the current page (for a fragment, the page it
        was loaded into).
    options
        The offered languages, in the order of ``supported_locales``.
    """

    action: str
    next: str
    options: tuple[LocaleOption, ...]


def _own_name(locale: str) -> str:
    tag = locale.replace("-", "_")
    name = Locale.parse(tag).get_display_name(tag) or locale
    return name[:1].upper() + name[1:]


def _current_path() -> str:
    request = RequestContext.get_request()
    url = request.headers.get("hx-current-url")
    if url:
        parts = urlsplit(url)
        return parts.path + (f"?{parts.query}" if parts.query else "")
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


def locale_switch() -> LocaleSwitch | None:
    """The data of a language switcher for the current request (headless).

    pyhx provides the behavior (the endpoint, storing the language) and this
    data; the app renders the switcher in its own design: buttons, a
    dropdown, entries of a user menu.

    Returns
    -------
    LocaleSwitch or None
        ``None`` outside a request or without a session (the user
        authentication addon registers the endpoint and the session), so
        there is nowhere to store a language.

    Examples
    --------
    >>> switch = locale_switch()
    >>> if switch:
    ...     y.form(method="post", action=switch.action, hx_post=switch.action)[
    ...         y.input(type="hidden", name="next", value=switch.next),
    ...         [
    ...             y.button(name="locale", value=o.locale, disabled=o.current)[o.name]
    ...             for o in switch.options
    ...         ],
    ...     ]
    """
    try:
        request = RequestContext.get_request()
    except LookupError, AssertionError:
        return None
    if "session" not in request.scope:
        return None
    current = negotiate_locale()
    return LocaleSwitch(
        action=LOCALE_SWITCH_PATH,
        next=_current_path(),
        options=tuple(
            LocaleOption(
                locale=locale, name=_own_name(locale), current=locale == current
            )
            for locale in LocaleSettings.read().supported_locales
        ),
    )
