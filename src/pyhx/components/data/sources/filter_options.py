"""Option tuples for each filter kind in :mod:`.filter`.

Each Option's ``value`` matches the ``kind`` discriminator of the
corresponding :class:`BaseFilterValue` subclass — so they can be fed
straight to a ``dropdown_radio``/``segment_control`` and the selected
value validated back into a ``FilterValue``.
"""

from pyhx.i18n import _p

from ...view_model import Option
from .filter_type import (
    BooleanFilter,
    ChoiceFilter,
    DateFilter,
    FilterType,
    ListChoiceFilter,
    NumericFilter,
    TextFilter,
)


def string_options() -> tuple[Option, ...]:
    """Operator options for :class:`TextFilter` columns."""
    return (
        Option(label=_p("filter operator", "equals"), value="string_equals"),
        Option(label=_p("filter operator", "contains"), value="string_contains"),
        Option(label=_p("filter operator", "starts with"), value="string_starts_with"),
        Option(label=_p("filter operator", "ends with"), value="string_ends_with"),
        Option(label=_p("filter operator", "is empty"), value="string_is_empty"),
        Option(
            label=_p("filter operator", "is not empty"), value="string_is_not_empty"
        ),
    )


def numeric_options() -> tuple[Option, ...]:
    """Operator options for :class:`NumericFilter` columns."""
    return (
        Option(label=_p("filter operator", "equals"), value="numeric_equals"),
        Option(
            label=_p("filter operator", "greater than"), value="numeric_greater_than"
        ),
        Option(
            label=_p("filter operator", "greater than or equal"),
            value="numeric_greater_than_or_equal",
        ),
        Option(label=_p("filter operator", "less than"), value="numeric_less_than"),
        Option(
            label=_p("filter operator", "less than or equal"),
            value="numeric_less_than_or_equal",
        ),
        Option(label=_p("filter operator", "between"), value="numeric_between"),
        Option(label=_p("filter operator", "is empty"), value="numeric_is_empty"),
        Option(
            label=_p("filter operator", "is not empty"), value="numeric_is_not_empty"
        ),
    )


def date_options() -> tuple[Option, ...]:
    """Operator options for :class:`DateFilter` columns."""
    return (
        Option(label=_p("filter operator", "equals"), value="date_equals"),
        Option(label=_p("filter operator", "before"), value="date_before"),
        Option(label=_p("filter operator", "after"), value="date_after"),
        Option(label=_p("filter operator", "between"), value="date_between"),
        Option(label=_p("filter operator", "is empty"), value="date_is_empty"),
        Option(label=_p("filter operator", "is not empty"), value="date_is_not_empty"),
    )


def bool_options() -> tuple[Option, ...]:
    """Operator options for :class:`BooleanFilter` columns."""
    return (
        Option(label=_p("filter operator", "is true"), value="bool_is_true"),
        Option(label=_p("filter operator", "is false"), value="bool_is_false"),
        Option(label=_p("filter operator", "is empty"), value="bool_is_empty"),
        Option(label=_p("filter operator", "is not empty"), value="bool_is_not_empty"),
    )


def single_choice_options() -> tuple[Option, ...]:
    """Operator options for single-select :class:`ChoiceFilter` columns."""
    return (
        Option(label=_p("filter operator", "equals"), value="text_choice_equals"),
        Option(label=_p("filter operator", "is empty"), value="text_choice_is_empty"),
        Option(
            label=_p("filter operator", "is not empty"),
            value="text_choice_is_not_empty",
        ),
    )


def multiple_choice_options() -> tuple[Option, ...]:
    """Operator options for multi-select :class:`ChoiceFilter` columns."""
    return (
        Option(label=_p("filter operator", "is any of"), value="text_choice_in"),
        Option(label=_p("filter operator", "is none of"), value="text_choice_not_in"),
        Option(label=_p("filter operator", "is empty"), value="text_choice_is_empty"),
        Option(
            label=_p("filter operator", "is not empty"),
            value="text_choice_is_not_empty",
        ),
    )


def list_options() -> tuple[Option, ...]:
    """Operator options for :class:`ListChoiceFilter` (list-valued) columns."""
    return (
        Option(label=_p("filter operator", "has any of"), value="list_intersects"),
        Option(label=_p("filter operator", "has all of"), value="list_contains_all"),
        Option(label=_p("filter operator", "has none of"), value="list_contains_none"),
        Option(label=_p("filter operator", "is empty"), value="list_is_empty"),
        Option(label=_p("filter operator", "is not empty"), value="list_is_not_empty"),
    )


def get_options_for_type(type: FilterType) -> tuple[Option, ...]:
    """Return the operator options appropriate for a column's filter type.

    Used by the filter drawer to populate the kind dropdown for a row —
    e.g. a numeric column's row offers ``equals``, ``greater than``,
    ``between``, …, while a date column offers ``before``, ``after``, etc.

    Parameters
    ----------
    type : FilterType
        The column's declared filter vocabulary.

    Returns
    -------
    tuple[Option, ...]
        Options whose ``value`` matches the corresponding
        ``BaseFilterValue.kind`` discriminator, ready to feed to
        ``dropdown_radio``.

    Raises
    ------
    ValueError
        If ``type`` doesn't match a known variant — guards against new
        filter types being added without a matching options tuple.
    """
    match type:
        case TextFilter():
            return string_options()
        case NumericFilter():
            return numeric_options()
        case DateFilter():
            return date_options()
        case BooleanFilter():
            return bool_options()
        case ChoiceFilter():
            return (
                multiple_choice_options() if type.multiple else single_choice_options()
            )
        case ListChoiceFilter():
            return list_options()
        case _:
            raise ValueError(f"No options defined for filter type: {type!r}")
