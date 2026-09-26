"""Filter operators (:data:`FilterValue`) and the per-field :class:`Condition`.

The model has two layers:

* :data:`FilterValue` is a discriminated union of every supported operator
  across string / numeric / date / boolean / choice columns
  (``StringEquals``, ``NumericBetween``, ``DateBefore``, …). Each variant
  carries the parameters its predicate needs (``value``, ``min``/``max``,
  or nothing for empty/not-empty checks).
* :class:`Condition` groups one or more :data:`FilterValue` operators
  against a single field. Multiple values within a ``Condition`` are
  combined with OR. The :class:`Query` decides how different fields
  combine via :attr:`Query.filter_mode`.

All variants share the ``kind`` discriminator so a serialized condition
can be round-tripped through JSON (e.g. the data table's hidden ``query``
input) without losing its variant.
"""

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_str_list(v: Any) -> Any:
    """Normalize a submitted multi-select value into a ``list[str]``.

    An HTML checkbox group submits *one* ``name=value`` pair per checked
    box: zero checked → the key is absent (``None``), exactly one → a bare
    ``str``, two or more → a list. This coerces the first two shapes so the
    operator always sees a list.
    """
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return v


class _StrListValues(BaseModel):
    """Mixin: a ``values: list[str]`` operator field that tolerates the
    scalar / missing shapes an HTML checkbox group submits."""

    values: list[str] = Field(default_factory=list)

    @field_validator("values", mode="before")
    @classmethod
    def _coerce_values(cls, v: Any) -> Any:
        return _coerce_str_list(v)


# =============================================================================
# 1) Filter Values
# =============================================================================


class BaseFilterValue(BaseModel):
    """Common configuration for every :data:`FilterValue` variant.

    ``extra="ignore"`` lets a stale serialized condition (one with an
    extra field that's since been dropped) still validate cleanly.
    """

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# 1.1) String Filter Values
# =============================================================================


class StringEquals(BaseFilterValue):
    """Filter for exact string match. Case-sensitive by default."""

    kind: Literal["string_equals"] = "string_equals"
    value: str


class StringContains(BaseFilterValue):
    """Filter for substring match. Matches if value contains the substring."""

    kind: Literal["string_contains"] = "string_contains"
    value: str


class StringStartsWith(BaseFilterValue):
    """Filter for prefix match. Matches if value starts with the prefix."""

    kind: Literal["string_starts_with"] = "string_starts_with"
    value: str


class StringEndsWith(BaseFilterValue):
    """Filter for suffix match. Matches if value ends with the suffix."""

    kind: Literal["string_ends_with"] = "string_ends_with"
    value: str


class StringIsEmpty(BaseFilterValue):
    """Filter for empty or null string values."""

    kind: Literal["string_is_empty"] = "string_is_empty"


class StringIsNotEmpty(BaseFilterValue):
    """Filter for non-empty, non-null string values."""

    kind: Literal["string_is_not_empty"] = "string_is_not_empty"


# =============================================================================
# 1.2) Numeric Filter Values
# =============================================================================


class NumericEquals(BaseFilterValue):
    """Filter for exact numeric match."""

    kind: Literal["numeric_equals"] = "numeric_equals"
    value: float | int


class NumericGreaterThan(BaseFilterValue):
    """Filter for values strictly greater than the threshold."""

    kind: Literal["numeric_greater_than"] = "numeric_greater_than"
    value: float | int


class NumericGreaterThanOrEqual(BaseFilterValue):
    """Filter for values greater than or equal to the threshold."""

    kind: Literal["numeric_greater_than_or_equal"] = "numeric_greater_than_or_equal"
    value: float | int


class NumericLessThan(BaseFilterValue):
    """Filter for values strictly less than the threshold."""

    kind: Literal["numeric_less_than"] = "numeric_less_than"
    value: float | int


class NumericLessThanOrEqual(BaseFilterValue):
    """Filter for values less than or equal to the threshold."""

    kind: Literal["numeric_less_than_or_equal"] = "numeric_less_than_or_equal"
    value: float | int


class NumericBetween(BaseFilterValue):
    """Filter for values within a range (inclusive on both ends)."""

    kind: Literal["numeric_between"] = "numeric_between"
    min: float | int
    max: float | int


class NumericIsEmpty(BaseFilterValue):
    """Filter for null numeric values."""

    kind: Literal["numeric_is_empty"] = "numeric_is_empty"


class NumericIsNotEmpty(BaseFilterValue):
    """Filter for non-null numeric values."""

    kind: Literal["numeric_is_not_empty"] = "numeric_is_not_empty"


# =============================================================================
# 1.3) Date Filter Values
# =============================================================================


class DateEquals(BaseFilterValue):
    """Filter for exact date match."""

    kind: Literal["date_equals"] = "date_equals"
    value: date


class DateBefore(BaseFilterValue):
    """Filter for dates strictly before the threshold."""

    kind: Literal["date_before"] = "date_before"
    value: date


class DateAfter(BaseFilterValue):
    """Filter for dates strictly after the threshold."""

    kind: Literal["date_after"] = "date_after"
    value: date


class DateBetween(BaseFilterValue):
    """Filter for dates within a range (inclusive on both ends)."""

    kind: Literal["date_between"] = "date_between"
    min: date
    max: date


class DateIsEmpty(BaseFilterValue):
    """Filter for null date values."""

    kind: Literal["date_is_empty"] = "date_is_empty"


class DateIsNotEmpty(BaseFilterValue):
    """Filter for non-null date values."""

    kind: Literal["date_is_not_empty"] = "date_is_not_empty"


# =============================================================================
# 1.4) Boolean Filter Values
# =============================================================================


class BoolIsTrue(BaseFilterValue):
    """Filter for true boolean values."""

    kind: Literal["bool_is_true"] = "bool_is_true"


class BoolIsFalse(BaseFilterValue):
    """Filter for false boolean values."""

    kind: Literal["bool_is_false"] = "bool_is_false"


class BoolIsEmpty(BaseFilterValue):
    """Filter for null boolean values."""

    kind: Literal["bool_is_empty"] = "bool_is_empty"


class BoolIsNotEmpty(BaseFilterValue):
    """Filter for non-null boolean values (either true or false)."""

    kind: Literal["bool_is_not_empty"] = "bool_is_not_empty"


# =============================================================================
# 1.5) Text Choice Filter Values
# =============================================================================


class TextChoiceEquals(BaseFilterValue):
    """Filter for exact match against one of the allowed values."""

    kind: Literal["text_choice_equals"] = "text_choice_equals"
    value: str


class TextChoiceIn(_StrListValues, BaseFilterValue):
    """Filter for a scalar value being *any of* a selected set (membership)."""

    kind: Literal["text_choice_in"] = "text_choice_in"


class TextChoiceNotIn(_StrListValues, BaseFilterValue):
    """Filter for a scalar value being *none of* a selected set (exclusion).

    The negation of :class:`TextChoiceIn`. An empty ``values`` is treated as
    *no constraint* (matches everything).
    """

    kind: Literal["text_choice_not_in"] = "text_choice_not_in"


class TextChoiceIsEmpty(BaseFilterValue):
    """Filter for null or empty choice values."""

    kind: Literal["text_choice_is_empty"] = "text_choice_is_empty"


class TextChoiceIsNotEmpty(BaseFilterValue):
    """Filter for non-null, non-empty choice values."""

    kind: Literal["text_choice_is_not_empty"] = "text_choice_is_not_empty"


# =============================================================================
# 1.6) List Filter Values (list-valued columns — set operations)
# =============================================================================


class ListIntersects(_StrListValues, BaseFilterValue):
    """Filter for a row's ``list`` value intersecting a selected set ("has any of").

    Matches when the row's list shares any value with ``values``. An empty
    ``values`` is treated as *no constraint* (matches everything) so an
    unselected multi-filter never hides every row.
    """

    kind: Literal["list_intersects"] = "list_intersects"


class ListContainsAll(_StrListValues, BaseFilterValue):
    """Filter for a row's ``list`` value being a *superset* of ``values`` ("has all of").

    Matches when the row's list contains *every* selected value. An empty
    ``values`` is treated as *no constraint* (the empty set is a subset of
    everything).
    """

    kind: Literal["list_contains_all"] = "list_contains_all"


class ListContainsNone(_StrListValues, BaseFilterValue):
    """Filter for a row's ``list`` value being *disjoint* from ``values`` ("has none of").

    The negation of :class:`ListIntersects`: matches when the row's list shares
    *no* value with ``values``. An empty ``values`` is treated as *no
    constraint* (matches everything).
    """

    kind: Literal["list_contains_none"] = "list_contains_none"


class ListIsEmpty(BaseFilterValue):
    """Filter for an empty / missing list value."""

    kind: Literal["list_is_empty"] = "list_is_empty"


class ListIsNotEmpty(BaseFilterValue):
    """Filter for a non-empty list value."""

    kind: Literal["list_is_not_empty"] = "list_is_not_empty"


FilterValue = Annotated[
    StringEquals
    | StringContains
    | StringStartsWith
    | StringEndsWith
    | StringIsEmpty
    | StringIsNotEmpty
    | NumericEquals
    | NumericGreaterThan
    | NumericGreaterThanOrEqual
    | NumericLessThan
    | NumericLessThanOrEqual
    | NumericBetween
    | NumericIsEmpty
    | NumericIsNotEmpty
    | DateEquals
    | DateBefore
    | DateAfter
    | DateBetween
    | DateIsEmpty
    | DateIsNotEmpty
    | BoolIsTrue
    | BoolIsFalse
    | BoolIsEmpty
    | BoolIsNotEmpty
    | TextChoiceEquals
    | TextChoiceIn
    | TextChoiceNotIn
    | TextChoiceIsEmpty
    | TextChoiceIsNotEmpty
    | ListIntersects
    | ListContainsAll
    | ListContainsNone
    | ListIsEmpty
    | ListIsNotEmpty,
    Field(discriminator="kind"),
]
"""Discriminated union of all filter condition types across all data types."""

# =============================================================================
# 2) Condition
# =============================================================================


class Condition(BaseModel):
    """A filter targeting a single field.

    Holds one *or more* :data:`FilterValue` operators against the same
    field. Multiple values are implicit-OR — they let a single field
    express clauses like *name equals "a" OR name contains "b"*. How
    different fields combine with each other is controlled separately by
    :attr:`Query.filter_mode`.

    Attributes
    ----------
    key : str
        Field identifier — matches a :attr:`Column.key`.
    values : list[FilterValue]
        Operators applied to the field. Combined with OR.
    """

    key: str
    values: list[FilterValue] = Field(default_factory=list)
