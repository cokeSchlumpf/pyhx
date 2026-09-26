import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Orientation


@component
def button_group(
    *buttons: y.Node,
    orientation: Orientation = "horizontal",
    **kwargs,
) -> y.Node:
    """Lay out a set of buttons in a row or a column.

    A pure flex layout wrapper — pass already-built ``button(...)`` nodes as
    positional children and they are arranged according to ``orientation``:

    * ``"horizontal"`` (default) — a row; each button keeps its natural width,
      separated by a small gap, wrapping to the next line if the row overflows.
    * ``"vertical"`` — a column; every button stretches to the same (container)
      width, separated by a small gap.

    Examples
    --------
    >>> button_group(button("Save", appearance="primary"), button("Cancel", variant="ghost"))
    >>> button_group(button("Edit"), button("Delete"), orientation="vertical")

    Parameters
    ----------
    *buttons : y.Node
        The button nodes to lay out (typically ``button(...)`` results, but any
        node works).
    orientation : Orientation, default "horizontal"
        ``"horizontal"`` lays buttons in a row at natural width; ``"vertical"``
        stacks them at equal width.
    **kwargs
        Forwarded to the wrapper ``<div>`` (e.g. ``class_=``, ``data-*``,
        ``role=``).
    """
    classes = ["hx-button-group", f"hx-button-group--{orientation}"]
    return y.div(**classnames(classes, **kwargs))[buttons]
