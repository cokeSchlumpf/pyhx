"""Column descriptors for :class:`DataTable`.

A :class:`Column` binds together how a column looks (``header``), how each
row's cell renders (``render``), how wide the column should be (``width``),
and how the column can be filtered (``filter_type``).
"""

from collections.abc import Callable
from dataclasses import dataclass

import htpy as y

from ..view_model.columns import ColumnKind, ColumnWidth, Flex
from .sources.filter_type import FilterType


@dataclass(frozen=True)
class Column[T]:
    """One column of a :class:`DataTable`.

    Parameters
    ----------
    key : str
        Stable identifier for the column. Used as the field key when sorting,
        filtering, and serializing the active query.
    label : str
        Human-readable name for the column. Shown in the filter drawer
        ("Sort by: <label>") and anywhere the column is referenced by name.
    header : y.Node
        Rendered table header cell content. Typically a plain string, but
        any ``htpy`` node is accepted.
    render : Callable[[T], y.Node]
        Cell renderer: receives one row item and returns the rendered cell
        content (usually a string, formatted value, or component).
    width : ColumnWidth, default Flex()
        Track sizing for this column. Defaults to ``Flex()`` — share
        leftover space evenly with other flex columns.
    filter_type : FilterType | None, default None
        Filter operator set supported on this column. ``None`` makes the
        column unfilterable (no entry in the filter drawer's "Add filter"
        dropdown). See :mod:`.sources.filter_type`.
    visible : bool, default True
        Whether the column renders as a ``<th>`` / ``<td>`` in the table.
        Non-visible columns are skipped by the renderer but still appear
        in the filter drawer and can be sorted programmatically.
    kind : ColumnKind | None, default None
        Semantic modifier applied as ``hx-table__cell--<kind>`` on
        both the header and body cells. Drives alignment + font features
        (e.g. ``"numeric"`` → right-aligned + tabular-nums). ``None``
        leaves cells unmodified.
    sortable : bool, default True
        Whether the column may be chosen as a sort key in the filter
        drawer's "Sort by" dropdown. ``False`` hides it there (mirroring how
        ``filter_type=None`` hides a column from the "Add filter" dropdown).
        This only gates the drawer UI — a column can still be sorted
        programmatically via a ``Query``.
    """

    key: str
    label: str
    header: y.Node
    render: Callable[[T], y.Node]
    width: ColumnWidth = Flex()
    filter_type: FilterType | None = None
    visible: bool = True
    kind: ColumnKind | None = None
    sortable: bool = True
