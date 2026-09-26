"""Per-column filter-type vocabulary.

A :data:`FilterType` describes *what kind of operators* a column supports
in the filter drawer (text, numeric, date, boolean, choice). It is set on
:attr:`Column.filter_type` and drives which entries appear in the kind
dropdown for that column — see :mod:`.filter_options`.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, PrivateAttr


class TextFilter(BaseModel):
    """Text column — string operators (equals, contains, starts with, …)."""

    kind: Literal["text"] = "text"


class NumericFilter(BaseModel):
    """Numeric column — comparison operators (=, >, <, between, …)."""

    kind: Literal["numeric"] = "numeric"


class DateFilter(BaseModel):
    """Date column — temporal operators (=, before, after, between, …)."""

    kind: Literal["date"] = "date"


class BooleanFilter(BaseModel):
    """Boolean column — predicate operators (is true, is false, is empty, …)."""

    kind: Literal["bool"] = "bool"


class ChoiceFilterOption(BaseModel):
    """One selectable value in a :class:`ChoiceFilter`.

    Attributes
    ----------
    label : str
        Human-readable label shown in the UI.
    value : str
        The value submitted by the form and stored on the filter.
    """

    label: str
    value: str


class ChoiceFilter(BaseModel):
    """Closed-set column — the user picks from a fixed list of choices.

    Attributes
    ----------
    choices : list[ChoiceFilterOption]
        The allowed values. Drives both the value-control dropdown and
        the choice operators (``equals``, ``in``) in the filter drawer.
        Materialized at render time when ``_choices_provider`` is set —
        see :attr:`_choices_provider`.

    Notes
    -----
    ``_choices_provider`` is a private (non-serialized) hook that the
    annotation reader attaches when the source :class:`TextChoiceFilter`
    holds a callable :data:`~pyhx.components.view_model.OptionsProvider`.
    The filter drawer awaits it at render time and substitutes a
    :class:`ChoiceFilter` whose ``choices`` are materialized for that
    request. Static-options markers leave ``_choices_provider`` ``None``
    and the eagerly-built ``choices`` list is used as-is.
    """

    kind: Literal["choice"] = "choice"
    choices: list[ChoiceFilterOption] = Field(default_factory=list)
    multiple: bool = False
    """Whether the user may select several values (multi-select) at once.

    Drives the operator set (``equals`` vs. ``is any of``) and the initial
    condition the drawer seeds. Set by the annotation reader from the source
    marker (:class:`TextChoiceFilter` → ``False``,
    :class:`MultipleChoiceFilter` → ``True``)."""
    _choices_provider: Any = PrivateAttr(default=None)
    _control: Any = PrivateAttr(default=None)
    """Annotation control marker (``.controls`` dataclass) picked by the
    developer. Isinstance-dispatched by the filter drawer to select the value
    widget. ``Any`` — like ``_choices_provider`` — so this data-layer module
    never imports the annotation controls."""


class ListChoiceFilter(BaseModel):
    """List-valued column — the row holds a ``list``; the filter is a closed set.

    Same closed-set choice vocabulary as :class:`ChoiceFilter`, but the match
    semantics are *set intersection*: a row matches when its list shares any
    value with the selected set. Always multi-select.
    """

    kind: Literal["listchoice"] = "listchoice"
    choices: list[ChoiceFilterOption] = Field(default_factory=list)
    multiple: bool = True
    _choices_provider: Any = PrivateAttr(default=None)
    _control: Any = PrivateAttr(default=None)


FilterType = Annotated[
    TextFilter
    | NumericFilter
    | DateFilter
    | BooleanFilter
    | ChoiceFilter
    | ListChoiceFilter,
    Field(discriminator="kind"),
]
"""Discriminated union of the per-column filter vocabularies."""
