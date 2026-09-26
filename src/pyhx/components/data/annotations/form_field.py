from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import htpy as y

from ...variants import Orientation
from ...view_model import OptionsProvider
from .controls import (
    CheckboxFieldsetControl,
    DrawerRadioControl,
    DrawerSelectControl,
    DropdownControl,
    MultiselectChoiceControl,
    RadioFieldsetControl,
    SegmentControl,
    TextChoiceControl,
    _default_to_choice_value,
)

__all__ = [
    "BooleanCheckboxFieldsetControl",
    "BooleanControl",
    "BooleanField",
    "BooleanRadioFieldsetControl",
    "BooleanSegmentControl",
    # Re-exported shared choice controls (canonical home: .controls)
    "CheckboxFieldsetControl",
    "DateField",
    "DrawerRadioControl",
    "DrawerSelectControl",
    "DropdownControl",
    "FormField",
    "HiddenField",
    # Field annotations
    "IgnoreField",
    "InputControl",
    "MultiselectChoiceControl",
    "MultiselectChoiceField",
    "NumericField",
    "RadioFieldsetControl",
    "SegmentControl",
    "TaglistControl",
    "TextChoiceControl",
    "TextChoiceField",
    "TextControl",
    "TextField",
    "TextListControl",
    "TextListField",
    # Form-only controls
    "TextareaControl",
    "WYSIWYGControl",
    "_default_to_choice_value",
]


# Controls


@dataclass(frozen=True, kw_only=True, init=False)
class TextareaControl:
    attributes: dict[str, y.Attribute] = field(default_factory=dict)

    def __init__(self, **attributes: y.Attribute) -> None:
        # frozen=True, so go through object.__setattr__
        object.__setattr__(self, "attributes", attributes)


@dataclass(frozen=True, kw_only=True, init=False)
class InputControl:
    attributes: dict[str, y.Attribute] = field(default_factory=dict)

    def __init__(self, **attributes: y.Attribute) -> None:
        # frozen=True, so go through object.__setattr__
        object.__setattr__(self, "attributes", attributes)


@dataclass(frozen=True, kw_only=True)
class WYSIWYGControl:
    pass


@dataclass(frozen=True, kw_only=True)
class BooleanSegmentControl:
    true_label: str = "Yes"
    false_label: str = "No"


@dataclass(frozen=True, kw_only=True)
class BooleanCheckboxFieldsetControl:
    label: str = "Yes"


@dataclass(frozen=True, kw_only=True)
class BooleanRadioFieldsetControl:
    true_label: str = "Yes"
    false_label: str = "No"
    orientation: Orientation = "vertical"


@dataclass(frozen=True, kw_only=True)
class TaglistControl:
    """Renders a :func:`taglist` for a free-form ``list[str]`` field.

    Only valid under :class:`TextListField`. ``known_values`` is an
    optional autocomplete pool; ``initial_tags`` is what surfaces in the
    dropdown before the user types; ``allow_new_tags`` toggles the
    Enter-commits-typed-text path."""

    known_values: OptionsProvider = ()
    initial_tags: OptionsProvider | None = None
    allow_new_tags: bool = True
    suggestions_label: str = "Suggested Tags"


TextControl = TextareaControl | InputControl | WYSIWYGControl
BooleanControl = (
    BooleanSegmentControl | BooleanCheckboxFieldsetControl | BooleanRadioFieldsetControl
)
TextListControl = TaglistControl


#
# Field annotations
#


@dataclass(frozen=True, kw_only=True)
class IgnoreField:
    """Marker: exclude this field from every form built off the model.

    The field never renders and never submits — use for internal/computed
    fields that share a model with form-driven ones. Unlike :class:`HiddenField`
    (which still submits a hidden ``<input>``), an ``IgnoreField`` field is
    dropped entirely by :func:`read_form_field_annotations`.
    """


@dataclass(frozen=True, kw_only=True)
class HiddenField:
    pass


@dataclass(frozen=True, kw_only=True)
class TextField:
    control: TextControl = InputControl()
    label: str | None = None
    help_text: str | None = None
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class NumericField:
    label: str | None = None
    help_text: str | None = None
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class BooleanField:
    control: BooleanControl = BooleanCheckboxFieldsetControl()
    label: str | None = None
    help_text: str | None = None
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class DateField:
    label: str | None = None
    help_text: str | None = None
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class TextChoiceField:
    control: TextChoiceControl
    label: str | None = None
    help_text: str | None = None
    to_choice_value: Callable[[Any], str] = _default_to_choice_value
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class MultiselectChoiceField:
    control: MultiselectChoiceControl
    label: str | None = None
    help_text: str | None = None
    to_choice_value: Callable[[Any], str] = _default_to_choice_value
    columns: int | None = None
    rows: int | None = None


@dataclass(frozen=True, kw_only=True)
class TextListField:
    """Free-form ``list[str]`` field.

    Differs from :class:`MultiselectChoiceField` in that values are NOT
    constrained to a closed pool — users can type arbitrary strings (when
    the control allows it). The control determines the rendering and
    interaction; currently only :class:`TaglistControl` is implemented.
    """

    control: TextListControl = field(default_factory=lambda: TaglistControl())
    label: str | None = None
    help_text: str | None = None
    columns: int | None = None
    rows: int | None = None


FormField = (
    HiddenField
    | TextField
    | NumericField
    | BooleanField
    | DateField
    | TextChoiceField
    | MultiselectChoiceField
    | TextListField
)
