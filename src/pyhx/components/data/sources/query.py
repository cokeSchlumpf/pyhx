"""The :class:`Query` model: a serializable sort + filter + paging spec.

Lives in its own module so the many components that depend on the query
shape (the data tables, the filter drawer, every data source) can import it
without dragging in the full data-source contract from :mod:`.source`. The
in-memory evaluation of a query against a ``list`` lives separately in
:mod:`._query` (``apply_query``).
"""

from typing import Literal

from pydantic import BaseModel, Field

from .filter import Condition
from .sort import SortOrder

FilterMode = Literal["all", "any"]
"""How per-field conditions combine. ``"all"`` is AND, ``"any"`` is OR."""


class Query(BaseModel):
    """A serializable view onto a data source: sort, filter, and paging.

    The shape is deliberately flat. Each entry in ``filter`` is a
    :class:`Condition` for a single field, and ``filter_mode`` decides how
    those per-field conditions are combined (``"all"`` → AND, ``"any"`` →
    OR). Within a single :class:`Condition`, multiple values are always
    OR-combined.

    Attributes
    ----------
    offset : int, default 0
        Number of items to skip from the start of the result set.
    limit : int | None, default None
        Maximum number of items to return. ``None`` means no limit.
    sort : list[SortOrder]
        Sort keys in priority order — the first is primary, the rest break
        ties.
    filter_mode : FilterMode, default "all"
        Root combinator for the per-field conditions in ``filter``.
    filter : list[Condition]
        Active filter conditions, one per filtered field.
    """

    offset: int = 0
    limit: int | None = None
    sort: list[SortOrder] = Field(default_factory=list)
    filter_mode: FilterMode = "all"
    filter: list[Condition] = Field(default_factory=list)

    def clear(self) -> None:
        """Resets sort and filter configurations. Does not reset offset and limit."""
        self.sort = []
        self.filter = []
        self.filter_mode = "all"

    def is_asc(self, key: str) -> bool:
        """Return ``True`` if the field ``key`` is currently sorted ascending."""
        return any(s.key == key and s.order == "asc" for s in self.sort)

    def is_desc(self, key: str) -> bool:
        """Return ``True`` if the field ``key`` is currently sorted descending."""
        return any(s.key == key and s.order == "desc" for s in self.sort)

    def is_active_filter(self, key: str) -> bool:
        """Return ``True`` if any active filter targets the field ``key``."""
        return any(c.key == key for c in self.filter)

    def is_active_filter_or_sort(self) -> bool:
        """Return ``True`` if any filter or sort configuratin is set."""
        return bool(self.sort or self.filter)

    def toggle_sort(self, key: str) -> None:
        """Cycle the sort state for ``key`` through asc → desc → asc.

        If ``key`` is the current sort field, flip its direction in place.
        Otherwise, replace the entire sort list with a single ascending
        sort on ``key`` — the common "click a column header" UX.

        Parameters
        ----------
        key : str
            The field name to toggle.
        """
        existing = next((s for s in self.sort if s.key == key), None)
        if existing and existing.order == "asc":
            existing.order = "desc"
        elif existing:
            existing.order = "asc"
        else:
            self.sort = [SortOrder(key=key, order="asc")]

    def extract(self, *keys: str) -> tuple["Query", "Query"]:
        """Split this query by field key into ``(remaining, extracted)``.

        ``extracted`` carries the sort and filter entries whose ``key`` is in
        ``keys``; ``remaining`` carries all the others. Use this to peel off
        conditions on calculated / non-repository fields so they can be applied
        in-memory while the repository handles the rest.

        ``remaining`` keeps this query's ``offset`` / ``limit`` (paging happens
        on the repository side); ``extracted`` resets them to ``0`` / ``None``.
        ``filter_mode`` is copied to both. All sort / filter entries are
        deep-copied, so neither result aliases this query's sub-objects.
        """
        keyset = set(keys)

        def split[I: (SortOrder, Condition)](items: list[I]) -> tuple[list[I], list[I]]:
            included = [i.model_copy(deep=True) for i in items if i.key in keyset]
            excluded = [i.model_copy(deep=True) for i in items if i.key not in keyset]
            return included, excluded

        ex_sort, rem_sort = split(self.sort)
        ex_filter, rem_filter = split(self.filter)
        remaining = Query(
            offset=self.offset,
            limit=self.limit,
            filter_mode=self.filter_mode,
            sort=rem_sort,
            filter=rem_filter,
        )
        extracted = Query(
            offset=0,
            limit=None,
            filter_mode=self.filter_mode,
            sort=ex_sort,
            filter=ex_filter,
        )
        return remaining, extracted
