"""Filter + sort + paging primitives shared by the in-memory data sources.

Both :class:`SimpleDataSource` (flat) and :class:`SimpleHierarchicalDataSource`
(per-level) need to evaluate a :class:`Query` against a ``list[T]`` in the
same way. The logic lives here once, with both classes calling :func:`apply_query`.
"""

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any

from .filter import (
    BoolIsEmpty,
    BoolIsFalse,
    BoolIsNotEmpty,
    BoolIsTrue,
    Condition,
    DateAfter,
    DateBefore,
    DateBetween,
    DateEquals,
    DateIsEmpty,
    DateIsNotEmpty,
    FilterValue,
    ListContainsAll,
    ListContainsNone,
    ListIntersects,
    ListIsEmpty,
    ListIsNotEmpty,
    NumericBetween,
    NumericEquals,
    NumericGreaterThan,
    NumericGreaterThanOrEqual,
    NumericIsEmpty,
    NumericIsNotEmpty,
    NumericLessThan,
    NumericLessThanOrEqual,
    StringContains,
    StringEndsWith,
    StringEquals,
    StringIsEmpty,
    StringIsNotEmpty,
    StringStartsWith,
    TextChoiceEquals,
    TextChoiceIn,
    TextChoiceIsEmpty,
    TextChoiceIsNotEmpty,
    TextChoiceNotIn,
)
from .query import Query


def value_of(item: Any, key: str) -> Any:
    """Read ``key`` off ``item``. Attribute access first (Pydantic models,
    dataclasses, plain classes); ``dict`` items fall back to key lookup.
    Returns ``None`` if the key is absent."""
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def count_matches(
    items: Sequence[Any],
    query: Query,
    *,
    value_of: Callable[[Any, str], Any] = value_of,
) -> int:
    """Count how many ``items`` would match ``query.filter``.

    Ignores ``query.sort`` (irrelevant to a count) and ``query.offset`` /
    ``query.limit`` (the count is the *matching total*, not the current
    page). Useful for paged or hierarchical sources that need to report
    how many children would survive the filter without materialising
    the full result.
    """
    if not query.filter:
        return len(items)
    return sum(1 for item in items if _matches_query(item, query, value_of))


def apply_query[T](
    items: Sequence[T],
    query: Query,
    *,
    value_of: Callable[[Any, str], Any] = value_of,
) -> tuple[list[T], int]:
    """Apply ``query`` (filter, sort, paging) to ``items`` in that order.

    Filter is evaluated first (no item is touched twice), then sort is
    applied (stable, lowest-priority first so the highest dominates), then
    ``offset`` / ``limit`` carve out the page. The returned ``total`` is the
    post-filter count — paging-aware UI uses it for "page X of Y".

    Parameters
    ----------
    items : Sequence[T]
        The candidates to evaluate against the query.
    query : Query
        Sort + filter + paging spec.
    value_of : Callable[[Any, str], Any], optional
        How to read a field off an item. Override only when the default
        attr-then-dict-key strategy doesn't fit (e.g. namespaced keys).

    Returns
    -------
    tuple[list[T], int]
        ``(page_items, post_filter_total)``.
    """
    filtered = [item for item in items if _matches_query(item, query, value_of)]
    # Stable sort: apply the lowest-priority sort first so the highest one
    # ends up dominant. ``query.sort`` lists priorities highest-first.
    for sort in reversed(query.sort):
        filtered.sort(
            key=_sort_key_for(sort.key, value_of),
            reverse=(sort.order == "desc"),
        )
    total = len(filtered)
    end = None if query.limit is None else query.offset + query.limit
    return filtered[query.offset : end], total


def _sort_key_for(
    key: str, value_of: Callable[[Any, str], Any]
) -> Callable[[Any], tuple[bool, Any]]:
    # (is_none, value): nulls sort after non-nulls. The ``0`` fallback keeps
    # two None items comparable without triggering a None < None TypeError on tie.
    def sort_key(item: Any) -> tuple[bool, Any]:
        v = value_of(item, key)
        return (v is None, v if v is not None else 0)

    return sort_key


def _matches_query(
    item: Any, query: Query, value_of: Callable[[Any, str], Any]
) -> bool:
    if not query.filter:
        return True
    per_field = [_matches_condition(item, c, value_of) for c in query.filter]
    if query.filter_mode == "all":
        return all(per_field)
    return any(per_field)


def _matches_condition(
    item: Any, cond: Condition, value_of: Callable[[Any, str], Any]
) -> bool:
    if not cond.values:
        return True
    field_value = value_of(item, cond.key)
    # Implicit OR within a field: any matching value satisfies the condition.
    return any(_matches_value(field_value, v) for v in cond.values)


def _as_date(v: Any) -> Any:
    """Reduce a ``datetime`` to its calendar ``date`` for day-granularity date
    filtering; pass everything else (including ``None``) through unchanged."""
    return v.date() if isinstance(v, datetime) else v


def _matches_value(value: Any, fv: FilterValue) -> bool:
    match fv:
        # String
        case StringEquals():
            return value == fv.value
        case StringContains():
            return value is not None and fv.value in str(value)
        case StringStartsWith():
            return value is not None and str(value).startswith(fv.value)
        case StringEndsWith():
            return value is not None and str(value).endswith(fv.value)
        case StringIsEmpty():
            return value is None or value == ""
        case StringIsNotEmpty():
            return value is not None and value != ""
        # Numeric
        case NumericEquals():
            return value == fv.value
        case NumericGreaterThan():
            return value is not None and value > fv.value
        case NumericGreaterThanOrEqual():
            return value is not None and value >= fv.value
        case NumericLessThan():
            return value is not None and value < fv.value
        case NumericLessThanOrEqual():
            return value is not None and value <= fv.value
        case NumericBetween():
            return value is not None and fv.min <= value <= fv.max
        case NumericIsEmpty():
            return value is None
        case NumericIsNotEmpty():
            return value is not None
        # Date — thresholds are date-only (drawer uses <input type="date">), so
        # a datetime cell is compared by its calendar date. Without this a
        # datetime would never equal a date (equals) and ordered comparisons
        # would raise TypeError.
        case DateEquals():
            return _as_date(value) == fv.value
        case DateBefore():
            return value is not None and _as_date(value) < fv.value
        case DateAfter():
            return value is not None and _as_date(value) > fv.value
        case DateBetween():
            return value is not None and fv.min <= _as_date(value) <= fv.max
        case DateIsEmpty():
            return value is None
        case DateIsNotEmpty():
            return value is not None
        # Boolean — ``is`` rather than ``==`` so ``1`` doesn't match ``True``.
        case BoolIsTrue():
            return value is True
        case BoolIsFalse():
            return value is False
        case BoolIsEmpty():
            return value is None
        case BoolIsNotEmpty():
            return value is not None
        # Text choice
        case TextChoiceEquals():
            return value == fv.value
        case TextChoiceIn():
            # Empty selection = no constraint (matches every row).
            return not fv.values or value in fv.values
        case TextChoiceNotIn():
            # Empty selection = no constraint (matches every row).
            return not fv.values or value not in fv.values
        case TextChoiceIsEmpty():
            return value is None or value == ""
        case TextChoiceIsNotEmpty():
            return value is not None and value != ""
        # List (list-valued columns — set operations)
        case ListIntersects():
            # Empty selection = no constraint (matches every row).
            return not fv.values or bool(set(value or ()) & set(fv.values))
        case ListContainsAll():
            # Empty selection = no constraint (empty set ⊆ anything).
            return set(fv.values) <= set(value or ())
        case ListContainsNone():
            # Empty selection = no constraint (empty intersection).
            return not (set(value or ()) & set(fv.values))
        case ListIsEmpty():
            return not value
        case ListIsNotEmpty():
            return bool(value)
        case _:
            raise ValueError(f"Unknown filter value: {fv!r}")
