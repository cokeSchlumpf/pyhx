from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

ContainerWidth = Literal["prose", "narrow", "medium", "wide", "stretch"]


@component
def container(
    children: y.Node,
    *,
    width: ContainerWidth = "medium",
    **kwargs,
) -> y.Node:
    """A horizontally-centered content wrapper with a max-width preset.

    Fills its parent up to the chosen ``width`` and stays centered via
    ``margin-inline: auto``. Use it to keep page content within a
    comfortable reading or layout width without committing the surrounding
    template to a fixed column.

    Parameters
    ----------
    width : ContainerWidth, default "medium"
        Maximum width preset.

        - ``"prose"`` — ``65ch``, ideal for body-text columns.
        - ``"narrow"`` — ``40rem`` (~640px).
        - ``"medium"`` — ``60rem`` (~960px).
        - ``"wide"`` — ``80rem`` (~1280px).
        - ``"stretch"`` — no max; container fills the parent.

    Examples
    --------
    >>> container(y.p["Long-form article body."], width="prose")
    >>> container(y.fragment[y.h1["Dashboard"], grid], width="wide")
    """
    return y.div(**classnames(["hx-container", f"hx-container--{width}"], **kwargs))[
        children
    ]
