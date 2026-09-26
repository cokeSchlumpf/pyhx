"""Column layout descriptors — shared view-model value types.

Pure value types (no rendering, no component dependencies) describing how a
column is sized and what semantic kind its cells are. Used by both the data
tables (:class:`pyhx.components.data.Column`) and the focus-list table variant,
so they live in the neutral ``view_model`` package that both layers import.
"""

from dataclasses import dataclass
from typing import Literal

ColumnKind = Literal["text", "numeric", "boolean", "date", "actions", "layout", "list"]
"""Semantic cell kind. Drives alignment, font features, and (later) colour
treatments via the ``hx-table__cell--<kind>`` modifier class. Add new
variants here as new cell treatments are introduced — e.g. ``"numeric-colored"``,
``"money"``, ``"code"``.

``"actions"`` is special: it lays out its contents as a right-aligned,
vertically-centred flex row (for a cluster of action buttons) and isolates
clicks within the cell from the row-level selection handler, so buttons don't
each need their own ``stopPropagation``.

``"layout"`` is special: it strips the cell's own flex layout and padding,
turning it into a plain block ``<td>`` so a self-contained layout (e.g. a
``hx-grid``) can be dropped in and own the full cell box."""


@dataclass(frozen=True)
class Fixed:
    """Fixed pixel width for a column track.

    Attributes
    ----------
    width : str
        Any valid CSS length (e.g. ``"60px"``, ``"4rem"``). Written into
        the table's ``grid-template-columns`` track for this column.
    """

    width: str


@dataclass(frozen=True)
class Flex:
    """Flexible width that grows proportionally with the available space.

    Renders as ``minmax(min_width, weight fr)``: the column will be at
    least ``min_width`` wide and otherwise distribute the remaining row
    width by its ``weight``.

    Attributes
    ----------
    weight : float, default 1.0
        Relative share of the leftover width once fixed columns have
        claimed theirs. A column with ``weight=2`` is twice as wide as
        one with ``weight=1``, all else equal.
    min_width : str, default "120px"
        Minimum CSS width before the column may grow.
    """

    weight: float = 1.0
    min_width: str = "120px"


ColumnWidth = Fixed | Flex
"""Width descriptor: either a fixed CSS length or a flex weight."""
