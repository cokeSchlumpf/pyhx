"""Annotation markers for data-driven UI generation.

These dataclasses are attached to :class:`pydantic.BaseModel` fields via
``Annotated[T, …]`` to describe how the field should appear in a generated
form, table, or detail view. They carry no runtime behaviour by themselves
— the form / table builders look them up via :func:`find_metadata` and
choose the right rendering primitive.

Two families live here:

* :mod:`.column` — markers for data-table columns
  (``TextColumn``, ``NumericColumn``, ``TextListColumn``, …) and their filter
  sub-types (``TextFilter``, ``TextChoiceFilter``, ``MultipleChoiceFilter``,
  ``TextListFilter``, ``NumericFilter``, ``DateFilter``, ``BooleanFilter``).
* :mod:`.form_field` — markers for form fields
  (``TextField``, ``BooleanField``, …) and their input controls
  (``InputControl``, ``TextareaControl``, ``DropdownControl``, …).
"""

from ...view_model import Option, OptionsProvider
from .column import (
    BooleanColumn,
    BooleanFilter,
    CurrencyNumberFormat,
    DateColumn,
    DateFilter,
    DateTimeColumn,
    HiddenColumn,
    IsoDateFormat,
    IsoNumberFormat,
    LocalizedDateFormat,
    LocalizedDateTimeFormat,
    LocalizedNumberFormat,
    MultipleChoiceFilter,
    NumericColumn,
    NumericFilter,
    PatternDateFormat,
    PatternNumberFormat,
    RelativeDateFormat,
    TextChoiceFilter,
    TextColumn,
    TextFilter,
    TextListColumn,
    TextListFilter,
)
from .form import FormConfig, SubmitLabel, form
from .form_field import (
    BooleanCheckboxFieldsetControl,
    BooleanControl,
    BooleanField,
    BooleanRadioFieldsetControl,
    BooleanSegmentControl,
    CheckboxFieldsetControl,
    DateField,
    DrawerRadioControl,
    DrawerSelectControl,
    DropdownControl,
    HiddenField,
    IgnoreField,
    InputControl,
    MultiselectChoiceControl,
    MultiselectChoiceField,
    NumericField,
    RadioFieldsetControl,
    SegmentControl,
    TaglistControl,
    TextareaControl,
    TextChoiceControl,
    TextChoiceField,
    TextControl,
    TextField,
    TextListControl,
    TextListField,
    WYSIWYGControl,
)

__all__ = [
    # --- Form-field control markers ---
    "BooleanCheckboxFieldsetControl",
    # --- Column annotations ---
    "BooleanColumn",
    # --- Control type aliases ---
    "BooleanControl",
    # --- Form-field annotations ---
    "BooleanField",
    "BooleanFilter",
    "BooleanRadioFieldsetControl",
    "BooleanSegmentControl",
    "CheckboxFieldsetControl",
    # --- Number formatting ---
    "CurrencyNumberFormat",
    "DateColumn",
    "DateField",
    "DateFilter",
    "DateTimeColumn",
    "DrawerRadioControl",
    "DrawerSelectControl",
    "DropdownControl",
    "FormConfig",
    "HiddenColumn",
    "HiddenField",
    "IgnoreField",
    "InputControl",
    # --- Date formatting ---
    "IsoDateFormat",
    "IsoNumberFormat",
    "LocalizedDateFormat",
    "LocalizedDateTimeFormat",
    "LocalizedNumberFormat",
    "MultipleChoiceFilter",
    "MultiselectChoiceControl",
    "MultiselectChoiceField",
    "NumericColumn",
    "NumericField",
    "NumericFilter",
    # --- Option types ---
    "Option",
    "OptionsProvider",
    "PatternDateFormat",
    "PatternNumberFormat",
    "RadioFieldsetControl",
    "RelativeDateFormat",
    "SegmentControl",
    "SubmitLabel",
    "TaglistControl",
    "TextChoiceControl",
    "TextChoiceField",
    "TextChoiceFilter",
    "TextColumn",
    "TextControl",
    "TextField",
    "TextFilter",
    "TextListColumn",
    "TextListControl",
    "TextListField",
    "TextListFilter",
    "TextareaControl",
    "WYSIWYGControl",
    # --- Class-level annotations ---
    "form",
]
