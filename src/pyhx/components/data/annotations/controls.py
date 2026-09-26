"""Choice-input control markers shared by form fields and table filters.

These describe *which widget* renders a closed-set choice — a dropdown, a
segmented control, a radio/checkbox fieldset, or a filterable drawer. They
are deliberately neutral: both :mod:`.form_field` (form inputs) and
:mod:`.column` (table filters) select a control from here, so neither
subsystem has to import the other.

Form-only controls (text, boolean, taglist) stay in :mod:`.form_field`.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...primitives.drawer_radio import DrawerRadioLabels
from ...primitives.drawer_select import DrawerSelectLabels
from ...variants import Orientation
from ...view_model import OptionsProvider


def _default_to_choice_value(v: Any) -> str:
    """Stringify a choice value for option / current-value rendering.

    Enum members render as their ``.value``; everything else falls through
    to ``str(v)``. Covers ``Literal[str]``, ``Literal[int]``, and ``Enum``
    subclasses without any per-field configuration.
    """
    if isinstance(v, Enum):
        return str(v.value)
    return str(v)


@dataclass(frozen=True, kw_only=True)
class SegmentControl:
    options: OptionsProvider


@dataclass(frozen=True, kw_only=True)
class RadioFieldsetControl:
    options: OptionsProvider
    orientation: Orientation = "vertical"


@dataclass(frozen=True, kw_only=True)
class CheckboxFieldsetControl:
    options: OptionsProvider
    orientation: Orientation = "vertical"


@dataclass(frozen=True, kw_only=True)
class DropdownControl:
    options: OptionsProvider


@dataclass(frozen=True, kw_only=True)
class DrawerRadioControl:
    """Renders a :func:`drawer_radio` for a single-select field.

    The single-selection counterpart of :class:`DrawerSelectControl`: built
    for long option pools where the choice is made in a filterable drawer
    rather than an inline dropdown or radio group. ``labels`` overrides the
    control's user-facing text — see :class:`DrawerRadioLabels`; when ``None``
    the component's defaults apply.
    """

    options: OptionsProvider
    labels: DrawerRadioLabels | None = None


@dataclass(frozen=True, kw_only=True)
class DrawerSelectControl:
    """Renders a :func:`drawer_select` for a multiselect field.

    Built for long option pools: instead of an inline list of checkboxes or
    a dropdown, the selection is edited in a filterable drawer. ``labels``
    overrides the control's user-facing text — see
    :class:`DrawerSelectLabels`; when ``None`` the component's defaults apply.
    """

    options: OptionsProvider
    labels: DrawerSelectLabels | None = None


TextChoiceControl = (
    SegmentControl | RadioFieldsetControl | DropdownControl | DrawerRadioControl
)
"""Single-select choice controls (used by ``TextChoiceField`` / ``TextChoiceFilter``)."""

MultiselectChoiceControl = (
    CheckboxFieldsetControl | DropdownControl | DrawerSelectControl
)
"""Multi-select choice controls (used by ``MultiselectChoiceField`` / multi filters)."""
