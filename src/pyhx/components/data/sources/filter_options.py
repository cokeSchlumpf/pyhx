"""Option tuples for each filter kind in :mod:`.filter`.

Each Option's ``value`` matches the ``kind`` discriminator of the
corresponding :class:`BaseFilterValue` subclass — so they can be fed
straight to a ``dropdown_radio``/``segment_control`` and the selected
value validated back into a ``FilterValue``.
"""

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

string_options = (
    Option(label="equals", value="string_equals"),
    Option(label="contains", value="string_contains"),
    Option(label="starts with", value="string_starts_with"),
    Option(label="ends with", value="string_ends_with"),
    Option(label="is empty", value="string_is_empty"),
    Option(label="is not empty", value="string_is_not_empty"),
)
"""Operator options for :class:`TextFilter` columns."""


numeric_options = (
    Option(label="equals", value="numeric_equals"),
    Option(label="greater than", value="numeric_greater_than"),
    Option(label="greater than or equal", value="numeric_greater_than_or_equal"),
    Option(label="less than", value="numeric_less_than"),
    Option(label="less than or equal", value="numeric_less_than_or_equal"),
    Option(label="between", value="numeric_between"),
    Option(label="is empty", value="numeric_is_empty"),
    Option(label="is not empty", value="numeric_is_not_empty"),
)
"""Operator options for :class:`NumericFilter` columns."""


date_options = (
    Option(label="equals", value="date_equals"),
    Option(label="before", value="date_before"),
    Option(label="after", value="date_after"),
    Option(label="between", value="date_between"),
    Option(label="is empty", value="date_is_empty"),
    Option(label="is not empty", value="date_is_not_empty"),
)
"""Operator options for :class:`DateFilter` columns."""


bool_options = (
    Option(label="is true", value="bool_is_true"),
    Option(label="is false", value="bool_is_false"),
    Option(label="is empty", value="bool_is_empty"),
    Option(label="is not empty", value="bool_is_not_empty"),
)
"""Operator options for :class:`BooleanFilter` columns."""


single_choice_options = (
    Option(label="equals", value="text_choice_equals"),
    Option(label="is empty", value="text_choice_is_empty"),
    Option(label="is not empty", value="text_choice_is_not_empty"),
)
"""Operator options for single-select :class:`ChoiceFilter` columns."""


multiple_choice_options = (
    Option(label="is any of", value="text_choice_in"),
    Option(label="is none of", value="text_choice_not_in"),
    Option(label="is empty", value="text_choice_is_empty"),
    Option(label="is not empty", value="text_choice_is_not_empty"),
)
"""Operator options for multi-select :class:`ChoiceFilter` columns."""


list_options = (
    Option(label="has any of", value="list_intersects"),
    Option(label="has all of", value="list_contains_all"),
    Option(label="has none of", value="list_contains_none"),
    Option(label="is empty", value="list_is_empty"),
    Option(label="is not empty", value="list_is_not_empty"),
)
"""Operator options for :class:`ListChoiceFilter` (list-valued) columns."""


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
            return string_options
        case NumericFilter():
            return numeric_options
        case DateFilter():
            return date_options
        case BooleanFilter():
            return bool_options
        case ChoiceFilter():
            return multiple_choice_options if type.multiple else single_choice_options
        case ListChoiceFilter():
            return list_options
        case _:
            raise ValueError(f"No options defined for filter type: {type!r}")
