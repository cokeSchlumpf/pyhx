"""Translate a :class:`Query` onto a SQLAlchemy ``Select`` statement.

Map UI-level field names to ORM columns once via a ``columns`` mapping,
then call :func:`apply_sql_query` to fold a :class:`Query`'s filter,
sort, and paging into the statement. The mapping decouples the UI
vocabulary from the DB schema — useful for renames, joins, and computed
columns.

The translation honours the same semantics as the in-memory query
evaluator:

* Multiple values within a single :class:`Condition` are OR-combined.
* Different conditions combine according to :attr:`Query.filter_mode`
  (``"all"`` → AND, ``"any"`` → OR).
* Sort applies stably in priority order (first key dominates).
* Paging applies ``offset`` and ``limit`` last.

Each :data:`FilterValue` variant maps to the SQLAlchemy operator that
matches its semantics — see :func:`_value_to_clause` for the exhaustive
mapping. Unknown variants and unmapped field keys are silently skipped
so a stale serialized query (one referencing a column that has since
been removed) doesn't crash the request.
"""

from collections.abc import Mapping
from typing import Any, TypeVar

from sqlalchemy import and_, or_
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.selectable import Select

from .filter import (
    BoolIsEmpty,
    BoolIsFalse,
    BoolIsNotEmpty,
    BoolIsTrue,
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

_S = TypeVar("_S", bound=Select[Any])
"""TypeVar bound to ``Select`` (not its inner row type) so subclasses
flow through unchanged.

Bound to the whole ``Select`` class — not its ``_TP`` row-shape
parameter — because sqlmodel's ``select(Org)`` returns a
``SelectOfScalar[Org]`` subclass, and ``session.exec`` is overloaded
specifically on ``SelectOfScalar`` for scalar reads. If we declared
``stmt: Select[_TP]`` instead, mypy would widen the return type to
plain ``Select[tuple[Org]]`` and the subsequent ``session.exec(stmt)``
would fail to type-check."""


type ColumnMap = Mapping[str, ColumnElement[Any]]
"""``{ui_field_name: sqlalchemy_column_expression}``.

The expression side is typically ``col(MyORM.field)`` for sqlmodel users
or ``MyORM.field`` for plain SQLAlchemy DeclarativeBase users; anything
producing a :class:`ColumnElement` works. Use :func:`columns_from_model`
for the simple "every model field, same name" case.
"""


def columns_from_model(model: type) -> dict[str, ColumnElement[Any]]:
    """Build a default :data:`ColumnMap` from every column on ``model``.

    Walks ``model.__table__.columns`` and returns
    ``{column.name: column}`` for each. Works for SQLModel
    ``table=True`` classes and SQLAlchemy ``DeclarativeBase`` subclasses
    alike — both expose ``__table__``.

    Caller can spread the result and override entries to handle renames
    or computed columns::

        {**columns_from_model(MyORM), "display_name": col(MyORM.raw_name)}
    """
    table = getattr(model, "__table__", None)
    if table is None:
        raise TypeError(
            f"{model!r} has no ``__table__`` — pass a SQLAlchemy / SQLModel "
            f"mapped class, or build the ColumnMap explicitly."
        )
    return {c.name: c for c in table.columns}


def apply_sql_query(
    stmt: _S,
    query: Query,
    columns: ColumnMap,
) -> _S:
    """Fold filter, sort, and paging from ``query`` onto ``stmt``.

    Convenience wrapper that calls :func:`apply_sql_filters`,
    :func:`apply_sql_sort`, and :func:`apply_sql_paging` in that order.
    Use the components directly when you only want a subset (e.g.,
    filters on a count query, filters + sort + paging on the rows
    query).
    """
    stmt = apply_sql_filters(stmt, query, columns)
    stmt = apply_sql_sort(stmt, query, columns)
    stmt = apply_sql_paging(stmt, query)
    return stmt


def apply_sql_filters(
    stmt: _S,
    query: Query,
    columns: ColumnMap,
) -> _S:
    """Append ``WHERE`` clauses for every condition in ``query.filter``."""
    if not query.filter:
        return stmt

    per_field_clauses: list[ColumnElement[bool]] = []
    for cond in query.filter:
        column = columns.get(cond.key)
        if column is None:
            continue
        value_clauses = [
            clause
            for v in cond.values
            if (clause := _value_to_clause(column, v)) is not None
        ]
        if value_clauses:
            per_field_clauses.append(or_(*value_clauses))

    if not per_field_clauses:
        return stmt

    combinator = and_ if query.filter_mode == "all" else or_
    return stmt.where(combinator(*per_field_clauses))


def apply_sql_sort(
    stmt: _S,
    query: Query,
    columns: ColumnMap,
) -> _S:
    """Append ``ORDER BY`` clauses for each entry in ``query.sort``.

    Sort entries are appended in priority order, so the first one
    dominates and later ones tie-break — matching the in-memory
    evaluator's semantics.
    """
    for so in query.sort:
        column = columns.get(so.key)
        if column is None:
            continue
        stmt = stmt.order_by(column.desc() if so.order == "desc" else column.asc())
    return stmt


def apply_sql_paging(stmt: _S, query: Query) -> _S:
    """Apply ``OFFSET`` / ``LIMIT`` from ``query`` to ``stmt``."""
    if query.offset:
        stmt = stmt.offset(query.offset)
    if query.limit is not None:
        stmt = stmt.limit(query.limit)
    return stmt


def _value_to_clause(
    column: ColumnElement[Any], value: FilterValue
) -> ColumnElement[bool] | None:
    """Map one :data:`FilterValue` to a SQLAlchemy boolean expression.

    Returns ``None`` for unrecognised variants so a forward-compat
    serialized query (carrying a new operator the deployed app doesn't
    know about yet) survives instead of crashing.
    """
    match value:
        # --- String ---
        case StringEquals():
            return column == value.value
        case StringContains():
            return column.contains(value.value)
        case StringStartsWith():
            return column.startswith(value.value)
        case StringEndsWith():
            return column.endswith(value.value)
        case StringIsEmpty():
            return or_(column.is_(None), column == "")
        case StringIsNotEmpty():
            return and_(column.is_not(None), column != "")

        # --- Numeric ---
        case NumericEquals():
            return column == value.value
        case NumericGreaterThan():
            return column > value.value
        case NumericGreaterThanOrEqual():
            return column >= value.value
        case NumericLessThan():
            return column < value.value
        case NumericLessThanOrEqual():
            return column <= value.value
        case NumericBetween():
            return column.between(value.min, value.max)
        case NumericIsEmpty():
            return column.is_(None)
        case NumericIsNotEmpty():
            return column.is_not(None)

        # --- Date ---
        case DateEquals():
            return column == value.value
        case DateBefore():
            return column < value.value
        case DateAfter():
            return column > value.value
        case DateBetween():
            return column.between(value.min, value.max)
        case DateIsEmpty():
            return column.is_(None)
        case DateIsNotEmpty():
            return column.is_not(None)

        # --- Boolean ---
        case BoolIsTrue():
            return column.is_(True)
        case BoolIsFalse():
            return column.is_(False)
        case BoolIsEmpty():
            return column.is_(None)
        case BoolIsNotEmpty():
            return column.is_not(None)

        # --- Text choice ---
        case TextChoiceEquals():
            return column == value.value
        case TextChoiceIn():
            # Empty selection = no constraint (skip this clause).
            return column.in_(value.values) if value.values else None
        case TextChoiceNotIn():
            # Empty selection = no constraint (skip this clause).
            return column.not_in(value.values) if value.values else None
        case TextChoiceIsEmpty():
            return or_(column.is_(None), column == "")
        case TextChoiceIsNotEmpty():
            return and_(column.is_not(None), column != "")

        # --- List (list-valued columns) ---
        # SQL is deferred: a UI list field maps to a single scalar
        # ``ColumnElement`` here, but a ``list`` value has no canonical scalar
        # column (JSON array / Postgres ARRAY / association table each need
        # bespoke SQL). Return ``None`` so the clause is skipped; SQL sources
        # should filter list columns via a custom ``ColumnMap``/app query.
        case (
            ListIntersects()
            | ListContainsAll()
            | ListContainsNone()
            | ListIsEmpty()
            | ListIsNotEmpty()
        ):
            return None

    return None
