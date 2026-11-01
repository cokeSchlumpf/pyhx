"""Quick filters and search of a :class:`~.data_table.DataTable`.

A quick filter is a named preset of filter conditions, shown as a pill
above the table. Presets don't live beside the table's :class:`Query`, they
are expressed in it: choosing a pill replaces the conditions on the preset
columns (every column a preset filters) with the preset's, and the active
pill is derived from the query's conditions. So the filter drawer, sorting
and search keep working on the same query, and a drawer change on a preset
column that matches no preset leaves no pill active ("custom").
"""

from collections.abc import Sequence
from dataclasses import dataclass

from pyhx.core.primitives.lazy_text import Text
from pyhx.i18n import _l

from .sources.filter import Condition
from .sources.query import Query

_QUICK_FILTERS_LABEL = _l("Quick filters")
_SEARCH_LABEL = _l("Search")


@dataclass(frozen=True, kw_only=True)
class QuickFilter:
    """One preset of a table's quick filters.

    Parameters
    ----------
    key : str
        Identifier of the preset, unique within the table. Written to the
        URL (``?view=<key>``) while the preset is active.
    label : Text
        Text of the pill (a ``str`` or a text marked with ``_l``).
    filter : Sequence[Condition], default ()
        The preset's conditions, at most one per column. A preset without
        conditions shows everything ("all") and is the one active on an
        unfiltered table; pass it first.
    """

    key: str
    label: Text
    filter: Sequence[Condition] = ()


@dataclass(frozen=True, kw_only=True)
class QuickFilters:
    """The quick filters of a table: presets shown as pills above the header.

    Parameters
    ----------
    presets : Sequence[QuickFilter]
        The pills, in display order.
    counts : bool, default False
        Show on each pill how many items the table would show after choosing
        it (``source.count``; a source that returns ``None`` shows no number).
        One count per preset and render, so only for sources that count
        cheaply.
    label : Text, default "Quick filters" (translated)
        Accessible name of the group of pills.
    url_param : str | None, default "view"
        URL parameter holding the active preset's key, so a link like
        ``/cases?view=open`` opens the table filtered. ``None`` keeps the
        quick filter out of the URL.

    Raises
    ------
    ValueError
        If two presets share a key, or a preset has two conditions on one
        column.
    """

    presets: Sequence[QuickFilter]
    counts: bool = False
    label: Text = _QUICK_FILTERS_LABEL
    url_param: str | None = "view"

    def __post_init__(self) -> None:
        keys = [p.key for p in self.presets]
        if len(keys) != len(set(keys)):
            raise ValueError(f"quick filter keys must be unique: {keys}")
        for preset in self.presets:
            columns = [c.key for c in preset.filter]
            if len(columns) != len(set(columns)):
                raise ValueError(
                    f"quick filter {preset.key!r} has more than one condition "
                    f"on a column: {columns}"
                )

    @property
    def columns(self) -> set[str]:
        """The preset columns: every column key any preset filters."""
        return {c.key for p in self.presets for c in p.filter}

    def find(self, key: str) -> QuickFilter | None:
        """The preset with ``key``, or ``None``."""
        return next((p for p in self.presets if p.key == key), None)


@dataclass(frozen=True, kw_only=True)
class TableSearch:
    """Texts and URL parameter of a table's search field.

    The field is shown when at least one column is searchable
    (``searchable=True``) and the source supports search.

    Parameters
    ----------
    label : Text, default "Search" (translated)
        Visible label of the field.
    placeholder : Text | None, default None
        Placeholder, e.g. the searchable columns' names.
    url_param : str | None, default "q"
        URL parameter holding the search term. ``None`` keeps the search out
        of the URL.
    """

    label: Text = _SEARCH_LABEL
    placeholder: Text | None = None
    url_param: str | None = "q"


def apply_quick_filter(
    query: Query, preset: QuickFilter, quick_filters: QuickFilters
) -> Query:
    """Return a copy of ``query`` with ``preset`` chosen.

    The conditions on the preset columns are replaced by the preset's;
    sort, search and the conditions on other columns stay.
    """
    columns = quick_filters.columns
    result = query.model_copy(deep=True)
    result.filter = [
        *(c for c in result.filter if c.key not in columns),
        *(c.model_copy(deep=True) for c in preset.filter),
    ]
    return result


def active_quick_filter(
    query: Query, quick_filters: QuickFilters
) -> QuickFilter | None:
    """The first preset whose conditions equal ``query``'s on the preset columns.

    ``None`` when they match no preset ("custom").
    """
    columns = quick_filters.columns
    current = {c.key: c.model_dump() for c in query.filter if c.key in columns}
    for preset in quick_filters.presets:
        if {c.key: c.model_dump() for c in preset.filter} == current:
            return preset
    return None
