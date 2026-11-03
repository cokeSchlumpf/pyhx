"""Small mark showing that something is happening right now.

``loading_indicator(label=...)`` renders a mark with no visible text, to be
placed next to a label, inside or beside a pill, in a button, in a table row
or in a navigation entry. It moves while it is rendered; when the work ends,
the app simply no longer renders it::

    loading_indicator(label="Saving")                          # spinner
    loading_indicator(label="Import running", kind="ripple", appearance="info")
    loading_indicator(label="Being processed", kind="pulse", size="sm")

Screen readers announce its ``label`` (``role="status"``). Which kind to use:

- ``spinner`` (the default): a turning arc, for short waits and inside
  buttons whose own action runs.
- ``ripple``: a dot sending out a ring, for something live or running, next
  to a status.
- ``pulse``: a dot that breathes, the quietest, for dense lists.
- ``dots``: three dots in turn, after a word ("Saving", "Waiting").
- ``bars``: three bars rising and falling, for busy work.

Nothing moves when the system asks for reduced motion; the mark stays
visible. To show how far the work has got, use
:data:`~pyhx.components.progress_bar`.
"""

from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Appearance, Size

type LoadingIndicatorKind = Literal["spinner", "ripple", "pulse", "dots", "bars"]
"""The shape and motion of a loading indicator: a turning arc (``spinner``),
a dot sending out a ring (``ripple``), a breathing dot (``pulse``), three dots
in turn (``dots``) or three rising bars (``bars``)."""

_PARTS = 3
"""Dots and bars are drawn from three parts; the other kinds need none."""


@component
def loading_indicator(
    *,
    label: str,
    kind: LoadingIndicatorKind = "spinner",
    appearance: Appearance = "primary",
    size: Size = "md",
    **kwargs: y.Attribute,
) -> y.Node:
    """Render a loading indicator.

    Parameters
    ----------
    label
        The accessible name, e.g. ``"Saving"`` or ``"Import running"``;
        announced by screen readers, not shown.
    kind
        The shape and motion: ``"spinner"`` (the default), ``"ripple"``,
        ``"pulse"``, ``"dots"`` or ``"bars"``; see the module for when to use
        which.
    appearance
        The colour of the mark; ``primary`` is the theme's primary colour (in
        the canvas design its text colour). Inside a solid button the mark
        takes the button's text colour.
    size
        ``sm`` next to 12-13px text and in table rows, ``md`` (the default)
        next to body text and pills, ``lg`` next to headings.
    **kwargs
        Additional HTML attributes forwarded to the root ``<span>``.

    Examples
    --------
    >>> c.button(["Saving", loading_indicator(label="Saving", size="sm")])
    >>> c.pill([loading_indicator(label="Import running", kind="ripple",
    ...                           appearance="info", size="sm"), "Import 35 %"])
    """
    parts = _PARTS if kind in ("dots", "bars") else 0
    return y.span(
        role="status",
        aria_label=label,
        **classnames(
            [
                "hx-loading-indicator",
                f"hx-loading-indicator--{kind}",
                f"hx-loading-indicator--{appearance}",
                f"hx-loading-indicator--{size}",
            ],
            **kwargs,
        ),
    )[[y.span(class_="hx-loading-indicator__part") for _ in range(parts)]]
