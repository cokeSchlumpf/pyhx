"""Compact tile for displaying a single metric.

A metric tile presents a prominent value together with a short label and
optional supporting text. It is intended for dashboard-style summaries such
as evidence coverage, open questions, changes, or completion counts.

The component only renders a supplied value. Calculating and formatting the
metric remains the responsibility of the calling application.
"""

from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Appearance

type MetricTileAppearance = Appearance | Literal["purple"]


@component
def metric_tile(
    *,
    value: y.Node,
    label: y.Node,
    supporting_text: y.Node | None = None,
    appearance: MetricTileAppearance = "neutral",
    **kwargs: y.Attribute,
) -> y.Node:
    """Render a compact metric tile.

    Parameters
    ----------
    value
        The prominently displayed metric, for example ``"92%"`` or ``"7"``.
        The caller is responsible for formatting the value.
    label
        A short description of the metric, such as ``"Evidence coverage"``.
    supporting_text
        Optional additional context displayed below the label.
    appearance
        Semantic colour variant used for the tile's accent and surface.
    **kwargs
        Additional HTML attributes forwarded to the outer ``<dl>``.

    Examples
    --------
    >>> metric_tile(
    ...     value="92%",
    ...     label="Evidence coverage",
    ...     appearance="info",
    ... )

    >>> metric_tile(
    ...     value="7",
    ...     label="Open questions",
    ...     supporting_text="Across all stages",
    ...     appearance="warning",
    ... )
    """
    return y.dl(
        **classnames(
            [
                "hx-metric-tile",
                f"hx-metric-tile--{appearance}",
            ],
            **kwargs,
        )
    )[
        y.dt(class_="hx-metric-tile__label")[label],
        y.dd(class_="hx-metric-tile__value")[value],
        (
            y.dd(class_="hx-metric-tile__supporting-text")[supporting_text]
            if supporting_text is not None
            else None
        ),
    ]
