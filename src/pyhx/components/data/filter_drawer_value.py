"""Data model for the filter drawer.

Extends :class:`Query` with the UI state the drawer round-trips through
forms (which view is active, which action button was clicked, etc.).
Because it is-a ``Query``, it can be passed directly to any ``ReadOnlyDataSource``
without conversion.
"""

from datetime import date
from typing import Literal

from .sources.filter import (
    BoolIsEmpty,
    Condition,
    DateAfter,
    ListIntersects,
    NumericEquals,
    StringContains,
    TextChoiceEquals,
    TextChoiceIn,
)
from .sources.filter_type import (
    BooleanFilter,
    ChoiceFilter,
    DateFilter,
    FilterType,
    ListChoiceFilter,
    NumericFilter,
    TextFilter,
)
from .sources.query import Query


class FilterDrawerValue(Query):
    """:class:`Query` plus the drawer's transient UI state.

    Parsed out of the drawer form on every htmx request. The non-Query
    fields below are *not* persisted to the data table's hidden query
    input — use :meth:`to_query` to strip them before handing the value
    off to anything that expects a pure ``Query``.

    Attributes
    ----------
    origin : Literal["drawer", "external"], default "external"
        Whether the value was reconstructed from the data table's hidden
        ``query`` input (``"external"``) or echoed back through the
        drawer's own form (``"drawer"``). Used by the drawer to decide
        whether to bootstrap from the persisted Query or trust the form.
    view : Literal["sort", "filter"], default "sort"
        Which tab the user is currently looking at.
    action : str | None
        The value of the last action button the user clicked
        (e.g. ``"apply"``, ``"clear"``, ``"add_filter_field"``,
        ``"remove_filter_condition <key> <idx>"``). ``None`` on the first
        render.
    add_filter_field : str | None
        The column key picked in the "Add filter" dropdown — read when
        ``action == "add_filter_field"``.
    add_sort_field : str | None
        The column key picked in the "Add sort" dropdown — read when
        ``action == "add_sort_field"``.
    """

    origin: Literal["drawer", "external"] = "external"
    view: Literal["sort", "filter"] = "sort"
    action: str | None = None

    add_filter_field: str | None = None
    add_sort_field: str | None = None

    def to_query(self) -> Query:
        """Strip drawer-only UI state and return a clean :class:`Query`.

        Use this before persisting the drawer's state (e.g. in the data
        table's hidden ``query`` input) or before handing the value off to
        any consumer that expects a pure ``Query`` — keeps ``origin``,
        ``view``, ``action``, etc. out of the serialized form.

        Returns
        -------
        Query
            A new ``Query`` carrying just ``offset``/``limit``/``sort``/
            ``filter_mode``/``filter``.
        """
        return Query.model_validate(self.model_dump())

    def add_filter(self, key: str, filter_type: FilterType) -> None:
        """Append a new filter row for ``key`` with a sensible initial value.

        Each filter type seeds a different default condition (e.g.
        ``"contains \"\""`` for a text column, ``equals 0`` for a number).
        Choice columns with no ``choices`` defined are silently skipped —
        there is no meaningful initial value to offer.

        Parameters
        ----------
        key : str
            The column key to start filtering on.
        filter_type : FilterType
            The column's filter vocabulary, used to pick the initial
            operator and value.
        """
        if isinstance(filter_type, TextFilter):
            self.filter.append(Condition(key=key, values=[StringContains(value="")]))
        elif isinstance(filter_type, NumericFilter):
            self.filter.append(Condition(key=key, values=[NumericEquals(value=0)]))
        elif isinstance(filter_type, DateFilter):
            self.filter.append(
                Condition(key=key, values=[DateAfter(value=date.today())])  # noqa: DTZ011 — local calendar date is the intended filter default
            )
        elif isinstance(filter_type, BooleanFilter):
            self.filter.append(Condition(key=key, values=[BoolIsEmpty()]))
        elif isinstance(f := filter_type, ChoiceFilter) and f.choices:
            first = f.choices[0].value
            seed = (
                TextChoiceIn(values=[first])
                if f.multiple
                else TextChoiceEquals(value=first)
            )
            self.filter.append(Condition(key=key, values=[seed]))
        elif isinstance(f := filter_type, ListChoiceFilter) and f.choices:
            self.filter.append(
                Condition(key=key, values=[ListIntersects(values=[f.choices[0].value])])
            )

    def clear(self) -> None:
        """Reset all filter and sort state to defaults.

        Wired to the drawer's "Clear" button. Leaves the UI state fields
        (``view``, ``action`` …) untouched — only the data is cleared.
        """
        self.filter = []
        self.sort = []
        self.filter_mode = "all"

    def remove_sort_key(self, key: str) -> None:
        """Drop any sort entries targeting ``key``."""
        self.sort = [s for s in self.sort if s.key != key]

    def remove_filter_key(self, key: str) -> None:
        """Drop the entire filter row for ``key`` (all of its conditions)."""
        self.filter = [f for f in self.filter if f.key != key]

    def remove_filter_condition(self, key: str, cond_idx: int) -> None:
        """Drop a single condition from the filter row for ``key``.

        No-op when ``key`` isn't filtered, or when ``cond_idx`` is out of
        range — protects against stale action strings being replayed from
        the form.

        Parameters
        ----------
        key : str
            The column key whose row to modify.
        cond_idx : int
            Zero-based index of the condition to drop within that row.
        """
        for f in self.filter:
            if f.key == key:
                if 0 <= cond_idx < len(f.values):
                    f.values.pop(cond_idx)
                return

    def add_filter_condition(self, key: str, filter_type: FilterType) -> None:
        """Append another condition to the existing filter row for ``key``.

        Mirrors the per-type defaults of :meth:`add_filter`. Silently
        no-ops when ``key`` isn't already a filter row — callers are
        expected to gate on that first.

        Parameters
        ----------
        key : str
            The column key whose row to extend.
        filter_type : FilterType
            The column's filter vocabulary, used to pick the initial
            operator and value for the new condition.
        """
        for f in self.filter:
            if f.key != key:
                continue
            if isinstance(filter_type, TextFilter):
                f.values.append(StringContains(value=""))
            elif isinstance(filter_type, NumericFilter):
                f.values.append(NumericEquals(value=0))
            elif isinstance(filter_type, DateFilter):
                f.values.append(DateAfter(value=date.today()))  # noqa: DTZ011 — local calendar date is the intended filter default
            elif isinstance(filter_type, BooleanFilter):
                f.values.append(BoolIsEmpty())
            elif isinstance(filter_type, ChoiceFilter) and filter_type.choices:
                first = filter_type.choices[0].value
                f.values.append(
                    TextChoiceIn(values=[first])
                    if filter_type.multiple
                    else TextChoiceEquals(value=first)
                )
            elif isinstance(filter_type, ListChoiceFilter) and filter_type.choices:
                f.values.append(ListIntersects(values=[filter_type.choices[0].value]))
            return
