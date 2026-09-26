import htpy as y

from pyhx.core import component
from pyhx.core.primitives import IconName, classnames

from ..primitives.button import button
from ..variants import Appearance


@component
def message(
    children: y.Node | None = None,
    *,
    appearance: Appearance = "info",
    title: str | None = None,
    icon: IconName | None = None,
    dismissible: bool = False,
    **kwargs,
) -> y.Node:
    """An inline message box (alert / callout) styled by appearance.

    Unlike :func:`notification` — which floats in a corner and is emitted via
    HTMX out-of-band swaps — a message lives in the normal page flow. It renders
    as a soft-tinted box with a coloured left accent, optional bold title, body
    content, an optional leading icon, and an optional close button.

    Buttons dropped into ``children`` adopt the message's appearance colour by
    default: a plain :func:`button` (which defaults to ``appearance="neutral"``)
    is re-themed to match the message via CSS. A button that passes an explicit
    non-neutral ``appearance`` keeps its own colour. Note that an *explicit*
    ``appearance="neutral"`` button is indistinguishable from a default one and
    therefore also adopts the message colour.

    Parameters
    ----------
    children
        Body content. Plain string, htpy nodes, or buttons.
    appearance
        Colour/semantic variant (info | success | warning | danger | neutral | primary).
    title
        Optional bold title rendered above ``children``.
    icon
        Optional leading feather icon (any :data:`IconName`). Omitted by
        default — pass e.g. ``icon="info"`` to show one.
    dismissible
        Render the X close button (default False). Dismissal is client-side —
        the button removes the closest ``.hx-message`` from the DOM.

    Examples
    --------
    >>> message("Your changes were saved.", appearance="success")
    >>> message("Check your input.", appearance="warning", title="Heads up")
    >>> message("Heads up.", appearance="info", icon="info")
    >>> message("Delete this item?", appearance="danger", dismissible=True)
    >>> message(["Update available.", button("View")], appearance="info")
    """
    close_btn: y.Node = (
        button(
            icon="x",
            aria_label="Dismiss",
            appearance="neutral",
            variant="ghost",
            size="md",
            onclick="this.closest('.hx-message').remove()",
        )
        if dismissible
        else None
    )

    return y.div(
        **classnames(["hx-message", f"hx-message--{appearance}"], **kwargs),
    )[
        # Wrap the feather placeholder so the replaced <svg> stays a *child*
        # of `.hx-message__icon` — feather.replace() copies the class onto the
        # svg, so a class placed directly on the <i> would move to the svg and
        # the `.hx-message__icon svg` sizing rule would no longer match.
        y.span(class_="hx-message__icon")[y.i(data_feather=icon)] if icon else None,
        y.div(class_="hx-message__body")[
            y.h4(class_="hx-message__title")[title] if title else None,
            y.div(class_="hx-message__content")[children],
        ],
        close_btn,
    ]
