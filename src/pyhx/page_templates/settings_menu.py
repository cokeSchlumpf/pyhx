"""The settings menu of the page templates: a gear in the header opening a dropdown."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import htpy as y

from pyhx.components.primitives.icon import icon
from pyhx.components.primitives.segment_control import segment_control
from pyhx.components.view_model import Option
from pyhx.core.primitives import IconName
from pyhx.core.primitives.lazy_text import Text
from pyhx.i18n import _, locale_switch


class SettingsEntry(Protocol):
    """One section of the settings menu.

    Called while the page is rendered; returns the section's markup, or
    ``None`` when it has nothing to show (the section is then left out, and
    the gear disappears when no section is left).
    """

    def __call__(self) -> y.Node: ...


@dataclass(frozen=True)
class SettingsLink:
    """A plain entry of the settings menu: a link with an optional icon.

    Attributes
    ----------
    label
        The text, e.g. ``_l("Sign out")``.
    href
        Where the link goes.
    icon
        A Feather icon name, e.g. ``"log-out"``.
    """

    label: Text
    href: str
    icon: IconName | None = None


class SettingsLinks:
    """Settings entry: a list of links, e.g. to the profile or to sign out.

    Examples
    --------
    >>> AppShell(settings=[
    ...     SettingsLinks(SettingsLink(_l("Sign out"), "/logout", icon="log-out")),
    ...     LanguageSetting(),
    ... ])

    For links that depend on the request (e.g. only for signed-in users),
    write an entry function that returns ``SettingsLinks(...)()`` or ``None``.
    """

    def __init__(self, *links: SettingsLink) -> None:
        self.links = links

    def __call__(self) -> y.Node:
        if not self.links:
            return None
        return y.ul(".hx-settings-menu__links")[
            (
                y.li[
                    y.a(href=link.href)[
                        icon(link.icon) if link.icon else None, y.span[link.label]
                    ]
                ]
                for link in self.links
            )
        ]


class LanguageSetting:
    """Settings entry: the language of the app.

    Shows the offered languages (``[app.pyhx.core] supported_locales``) as
    codes (EN | DE | IT | FR) in a ``segment_control``, the current one
    selected and written out above. Choosing one posts to ``/_pyhx/locale``
    (htmx, on change) (see
    :func:`pyhx.i18n.locale_switch`), which stores it in the session and, for
    a signed-in registered user, on the user, then reloads the page.

    Renders nothing with fewer than two languages or without a session.
    """

    def __call__(self) -> y.Node:
        switch = locale_switch()
        if switch is None or len(switch.options) < 2:
            return None
        current = next((o.name for o in switch.options if o.current), "")
        return y.section(
            ".hx-settings-menu__section", aria_labelledby="hx-settings-language"
        )[
            y.div(".hx-settings-menu__heading")[
                y.h2(id="hx-settings-language")[_("Language")],
                y.span[current],
            ],
            y.form(
                method="post",
                action=switch.action,
                hx_post=switch.action,
                hx_trigger="change",
            )[
                y.input(type="hidden", name="next", value=switch.next),
                segment_control(
                    "locale",
                    [
                        Option(label=o.locale.split("-")[0].upper(), value=o.locale)
                        for o in switch.options
                    ],
                    value=next((o.locale for o in switch.options if o.current), None),
                    aria_labelledby="hx-settings-language",
                ),
            ],
        ]


DEFAULT_SETTINGS: tuple[SettingsEntry, ...] = (LanguageSetting(),)
"""The settings menu of a page template unless the app passes ``settings=``."""


def settings_menu(entries: Sequence[SettingsEntry]) -> y.Node:
    """The gear with its dropdown, or ``None`` when no entry has anything to show."""
    sections = [section for entry in entries if (section := entry()) is not None]
    if not sections:
        return None
    return y.details(".hx-settings-menu")[
        y.summary(aria_label=_("Settings"), title=_("Settings"))[icon("settings")],
        y.div(".hx-settings-menu__panel")[sections],
    ]
