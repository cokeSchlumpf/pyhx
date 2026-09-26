import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


@component
def notification_badge(
    children: y.Node, *, count: int, max: int = 99, **kwargs
) -> y.Node:
    """Overlay a small red unread-count bubble on the top-right corner of
    ``children`` — the iOS/WhatsApp convention. Works on any wrapped node (a
    button, an icon, ...), not just buttons: it just wraps ``children`` in a
    positioning container and layers the bubble on top via absolute
    positioning, so the wrapped content itself needs no changes.

    Renders ``children`` alone, no bubble, when ``count`` is 0 - a caller
    doesn't need to conditionally call this itself.

    Parameters
    ----------
    children
        The node to badge - typically a button or icon.
    count
        The unread/pending count to display. 0 renders no badge at all.
    max
        Above this, the badge shows ``"{max}+"`` instead of the exact count,
        so a large number never breaks the badge's fixed circular shape.

    Examples
    --------
    >>> notification_badge(
    ...     c.button("Todos", icon="check-square", **htmx(hx_get=..., hx_swap="none")),
    ...     count=open_todo_count,
    ... )
    """
    label = str(count) if count <= max else f"{max}+"
    return y.span(**classnames("hx-notification-badge-wrapper", **kwargs))[
        children,
        y.span(class_="hx-notification-badge")[label] if count > 0 else None,
    ]
