"""Read-only bar showing how far a piece of work has got.

``progress_bar(value)`` renders a track with a filled part covering
``value`` (a :class:`~pyhx.components.view_model.Pct`), with the semantics
of a progress bar (``role="progressbar"``), optionally with a label and a
value text above and a supporting line below::

    progress_bar(Pct(0.35))                                  # static
    progress_bar(Pct(0.35), working=True, label="Analysing", value_text="35 %")
    progress_bar(Pct.clamp(done / total), working=True, motion="stripes")
    progress_bar(None, label="Waiting, 2nd in line")         # waiting

Three modes: **static** (nothing moves), **working** (the filled part moves:
``motion`` ``"sheen"``, ``"stripes"`` or ``"pulse"``) and **waiting**
(``value=None``: a segment travels along the track). Nothing moves when the
system asks for reduced motion. For a value the user sets, use
:data:`~pyhx.components.slider`.
"""

from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Appearance, Size
from ..view_model import Pct

type ProgressMotion = Literal["sheen", "stripes", "pulse"]
"""How the filled part of a working bar moves: a light band sweeping across
it (``sheen``), diagonal stripes running along it (``stripes``) or fading in
and out (``pulse``)."""


@component
def progress_bar(
    value: Pct | None,
    *,
    working: bool = False,
    motion: ProgressMotion = "sheen",
    label: y.Node = None,
    value_text: y.Node = None,
    supporting_text: y.Node = None,
    appearance: Appearance = "primary",
    size: Size = "md",
    aria_label: str | None = None,
    **kwargs: y.Attribute,
) -> y.Node:
    """Render a progress bar.

    Parameters
    ----------
    value
        How far the work has got, or ``None`` while its amount is unknown
        (waiting: a segment travels along the track).
    working
        Whether the work is in progress: the filled part moves as chosen by
        ``motion``. A static bar (the default) doesn't move.
    motion
        The movement of a working bar: ``"sheen"`` (calm, the default),
        ``"stripes"`` (visible from afar) or ``"pulse"`` (quiet).
    label
        Shown above the bar on the left, e.g. ``"Extracting findings"``; its
        accessible name when it is a string.
    value_text
        Shown above the bar on the right, e.g. ``"35 %"`` or ``"7 of 10"``;
        announced instead of the percentage when it is a string.
    supporting_text
        Shown below the bar, e.g. ``"Page 4 of 12 · about 3 min left"``.
    appearance
        The colour of the filled part; ``primary`` is the theme's primary
        colour (in the canvas design its text colour).
    size
        The height of the bar: ``sm`` (4px, e.g. in a table cell), ``md``
        (8px) or ``lg`` (12px).
    aria_label
        The accessible name, when ``label`` is not a plain string or not
        shown.
    **kwargs
        Additional HTML attributes forwarded to the root ``<div>``. Give the
        bar an ``id`` when htmx replaces it (e.g. a server-sent event with a
        new value): the filled part then glides to the new value instead of
        jumping.

    Examples
    --------
    >>> progress_bar(Pct.of(70), label="Upload", value_text="7 of 10 files")
    >>> progress_bar(Pct(1.0), appearance="success", supporting_text="Done")
    """
    waiting = value is None
    moving = working and not waiting

    name = aria_label if aria_label is not None else label
    track_attrs: dict[str, str] = {
        "class": "hx-progress-bar__track",
        "role": "progressbar",
    }
    if isinstance(name, str):
        track_attrs["aria-label"] = name
    if value is not None:
        track_attrs["aria-valuemin"] = "0"
        track_attrs["aria-valuemax"] = "100"
        track_attrs["aria-valuenow"] = str(round(value.percent))
        if isinstance(value_text, str):
            track_attrs["aria-valuetext"] = value_text
    if moving or waiting:
        track_attrs["aria-busy"] = "true"

    # With an id, the fill of a bar with a value gets a stable id too: when
    # htmx swaps in a new bar (e.g. from a server-sent event), it settles the
    # fill's old style into the new one, so the width change runs as a CSS
    # transition. A waiting bar's segment gets none: the first value appears
    # at once instead of the segment shrinking to it.
    fill_attrs: dict[str, str] = {"class": "hx-progress-bar__fill"}
    if value is not None:
        if isinstance(kwargs.get("id"), str):
            fill_attrs["id"] = f"{kwargs['id']}-fill"
        fill_attrs["style"] = f"--progress-bar--value: {value}"
    fill = y.div(fill_attrs)

    has_head = label is not None or value_text is not None

    return y.div(
        **classnames(
            {
                "hx-progress-bar": True,
                f"hx-progress-bar--{appearance}": True,
                f"hx-progress-bar--{size}": True,
                "hx-progress-bar--working": moving,
                f"hx-progress-bar--{motion}": moving,
                "hx-progress-bar--waiting": waiting,
            },
            **kwargs,
        )
    )[
        (
            y.div(class_="hx-progress-bar__head")[
                y.span(class_="hx-progress-bar__label")[label],
                y.span(class_="hx-progress-bar__value")[value_text],
            ]
            if has_head
            else None
        ),
        y.div(track_attrs)[fill],
        (
            y.div(class_="hx-progress-bar__supporting-text")[supporting_text]
            if supporting_text is not None
            else None
        ),
    ]
