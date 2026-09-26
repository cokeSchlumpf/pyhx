"""The skeleton ``<div class="hx-gantt">`` container built by ``gantt(...)``."""

import htpy as y

from ....core.primitives import classnames as cx
from .._element import _HxElement


class _KxGantt(_HxElement):
    """A ``<div class="hx-gantt">`` container — the skeleton Gantt chart.

    Built via the :data:`gantt` factory — ``gantt(...)`` sets options and
    ``gantt[...]`` supplies the children. No timeline behaviour is wired up yet;
    the container simply renders its children inside the BEM root class.
    """

    def __init__(
        self,
        *,
        children: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        """Configure the chart.

        Args:
            children: The chart's content.
            **kwargs: Extra HTML attributes forwarded to the ``<div>``.
        """
        self._children = children
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return y.div(**cx("hx-gantt", **self._kwargs))[self._children]
