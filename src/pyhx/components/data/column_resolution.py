"""Resolve the final column tuple for a data table or filter drawer.

Shared by :class:`~pyhx.components.data.data_table.DataTable`, the
hierarchical table, and :class:`~pyhx.components.data.filter_drawer.FilterDrawer`
so they all derive columns identically. Lives in its own module (rather
than in ``_table_helpers``) so the filter drawer can import it without a
circular dependency.
"""

from typing import cast

from pydantic import BaseModel

from .annotations.reader import read_column_annotations
from .column import Column


def resolve_columns[T](
    *,
    explicit: tuple[Column[T], ...] | None = None,
    type: type | None = None,
    columns_order: list[str] | None = None,
) -> tuple[Column[T], ...]:
    """Resolve the final tuple of columns for a data table.

    Merges columns auto-derived from a Pydantic model's annotated fields
    (see :func:`read_column_annotations`) with the explicit ``columns``
    tuple — typically action columns or per-call overrides. On key
    collision, explicit columns win.

    ``columns_order`` is the authoritative whitelist and order when set:
    any column whose key is absent is dropped from the table. Without
    it, derived columns come first (in model field order) and explicit
    columns are appended in call order.

    Used by the flat :class:`~.data_table.DataTable`, the hierarchical
    :class:`~.hierarchical_data_table.HierarchicalDataTable`, and the
    :class:`~.filter_drawer.FilterDrawer` so they stay in lock-step on
    column derivation behaviour.
    """
    explicit_columns = explicit or ()
    derived: dict[str, Column[T]] = (
        cast(dict[str, Column[T]], read_column_annotations(type))
        if type is not None and issubclass(type, BaseModel)
        else {}
    )
    explicit_by_key: dict[str, Column[T]] = {c.key: c for c in explicit_columns}
    all_columns = {**derived, **explicit_by_key}

    if columns_order is not None:
        return tuple(all_columns[k] for k in columns_order if k in all_columns)
    return tuple(all_columns.values())
