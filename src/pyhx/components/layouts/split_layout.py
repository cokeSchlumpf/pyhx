"""Two-column layout: a main column and a sticky aside on the right.

The aside sticks below whatever the page template pins to the top of the
viewport (``--hx-sticky-top``: the top bar, plus the page header in
:class:`~pyhx.page_templates.AppShell`) while the main column scrolls. When
the layout itself gets narrower than 58rem, it stacks into one column and the
aside scrolls with the page. The breakpoint is a container query, so it
follows the space the layout actually has (e.g. next to AppShell's sidebar),
not the viewport.
"""

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


@component
def split_layout(*, main: y.Node, aside: y.Node, **kwargs) -> y.Node:
    """Render a main column with a sticky aside column on the right.

    The outer element is the size container; the grid sits inside it because
    a container query only styles the container's descendants.

    Parameters
    ----------
    main : Node
        Content of the main (left) column.
    aside : Node
        Content of the aside (right) column. It is capped at the viewport
        height below the sticky bars and scrolls on its own when longer.

    Examples
    --------
    >>> split_layout(
    ...     main=y.fragment[overview_card, documents_card],
    ...     aside=history_card,
    ... )
    """
    return y.div(**classnames("hx-split-layout", **kwargs))[
        y.div(class_="hx-split-layout__grid")[
            y.div(class_="hx-split-layout__main")[main],
            y.aside(class_="hx-split-layout__aside")[aside],
        ]
    ]
