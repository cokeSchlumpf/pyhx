import uuid

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import IconName, classnames, merge_styles

from ..primitives.button import button
from ..variants import Appearance

NOTIFICATIONS_CONTAINER_ID = "hx-notifications"


_DEFAULT_ICONS: dict[Appearance, IconName] = {
    "info": "info",
    "success": "check-circle",
    "warning": "alert-triangle",
    "danger": "alert-octagon",
    "neutral": "message-square",
    "primary": "info",
}


@component
def notification_card(
    *,
    id: str = "",
    appearance: Appearance = "info",
    title: str | None = None,
    icon: IconName = "info",
    dismissible: bool = True,
    timeout_ms: int | None = None,
    children: y.Node | None = None,
    **kwargs,
) -> y.Node:
    """Inner notification card markup, without the OOB-swap outer wrapper.

    Public building block exposed for callers that need the card markup
    independent of the live append-via-OOB flow — e.g. a page template that
    renders one inside a ``<template>`` element so a client-side handler can
    clone it on htmx error events.

    Title and content slots are always rendered (so JS template-clones can
    fill the text nodes); empty slots are hidden by ``:empty`` CSS rules.
    """
    card_extras: dict[str, str] = {}
    if timeout_ms is not None:
        # `hx-on::load` (double colon = the `htmx:load` event) fires when
        # htmx inserts the element. The plain DOM `load` event doesn't fire
        # on arbitrary <div>s.
        card_extras["hx-on::load"] = (
            f"setTimeout(() => this.remove(), {int(timeout_ms)})"
        )

    close_btn: y.Node = (
        button(
            icon="x",
            aria_label="Dismiss",
            appearance="neutral",
            variant="ghost",
            size="md",
            onclick="this.closest('.hx-notification').remove()",
        )
        if dismissible
        else None
    )

    return y.div(
        id=id,
        **card_extras,
        **classnames(["hx-notification", f"hx-notification--{appearance}"], **kwargs),
    )[
        y.i(class_="hx-notification__icon", data_feather=icon),
        y.div(class_="hx-notification__body")[
            y.h4(class_="hx-notification__title")[title or ""],
            y.div(class_="hx-notification__content")[children],
        ],
        close_btn,
    ]


@component
def notifications(top: str = "0px", **kwargs) -> y.Node:
    """Mount point for floating notification messages. Render once in the page shell.

    Notification items emitted from fragment handlers are prepended here via
    HTMX out-of-band swaps (``hx-swap-oob="afterbegin:#hx-notifications"``).
    """
    return y.div(
        id=NOTIFICATIONS_CONTAINER_ID,
        aria_live="polite",
        aria_atomic="false",
        **classnames(
            "hx-notifications",
            **merge_styles({"--hx-notifications--top": top}, **kwargs),
        ),
    )


@component
def notification(
    children: y.Node | None = None,
    *,
    id: str | None = None,
    appearance: Appearance = "info",
    title: str | None = None,
    icon: IconName | None = None,
    timeout: int | None = None,
    dismissible: bool = True,
    **kwargs,
) -> y.Node:
    """A single floating notification (toast).

    Renders with ``hx-swap-oob="afterbegin:#hx-notifications"`` so each emitted
    item prepends to the stack (newest closest to the viewport edge) rather
    than replacing it. Emit from any fragment response alongside your in-band
    content::

        return [main_response, notification("Saved.", appearance="success", timeout=4000)]

    Parameters
    ----------
    children
        Body content. Plain string or htpy nodes.
    id
        Optional DOM id; auto-generated when omitted.
    appearance
        Color/semantic variant (info | success | warning | danger | neutral | primary).
    title
        Optional bold title rendered above ``children``.
    icon
        Override the default feather icon (defaults are picked per appearance).
    timeout
        Auto-dismiss after this many milliseconds. ``None`` (default) = persistent.
    dismissible
        Render the X close button (default True).
    """
    id = id or f"hx-notification-{uuid.uuid4().hex[:8]}"
    icon_name: IconName = icon or _DEFAULT_ICONS[appearance]

    # Positional OOB swaps (`afterbegin:#target`) insert the swap element's
    # *children* at the target — the element itself is discarded. The outer
    # wrapper here gets consumed; the inner card from `notification_card`
    # lands inside `#hx-notifications`.
    return y.div(**{"hx-swap-oob": f"afterbegin:#{NOTIFICATIONS_CONTAINER_ID}"})[
        notification_card(
            id=id,
            appearance=appearance,
            title=title,
            icon=icon_name,
            dismissible=dismissible,
            timeout_ms=timeout,
            children=children,
            **kwargs,
        ),
    ]
