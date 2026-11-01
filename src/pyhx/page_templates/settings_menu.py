"""The settings menu of the page templates: a gear in the header opening a dropdown."""

from collections.abc import Sequence
from typing import Protocol

import htpy as y

from pyhx.components.primitives.icon import icon
from pyhx.i18n import _, locale_switch


class SettingsEntry(Protocol):
    """One section of the settings menu.

    Called while the page is rendered; returns the section's markup, or
    ``None`` when it has nothing to show (the section is then left out, and
    the gear disappears when no section is left).
    """

    def __call__(self) -> y.Node: ...


class LanguageSetting:
    """Settings entry: the language of the app.

    Shows the offered languages (``[app.pyhx.core] supported_locales``) as
    codes (EN | DE | IT | FR), the current one highlighted and written out
    above. Choosing one posts to ``/_pyhx/locale`` (see
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
                ".hx-settings-menu__choices",
                method="post",
                action=switch.action,
                hx_post=switch.action,
            )[
                y.input(type="hidden", name="next", value=switch.next),
                [
                    y.button(
                        type="submit",
                        name="locale",
                        value=option.locale,
                        lang=option.locale,
                        title=option.name,
                        aria_pressed="true" if option.current else "false",
                    )[option.locale.split("-")[0].upper()]
                    for option in switch.options
                ],
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
