"""Shared view-model value types.

Presentation-oriented value types reused across components — column layout
descriptors and selectable options. The package is neutral (depends on nothing
in ``data`` / ``primitives`` / ``layouts``), so both layers can import down into
it without inverting the dependency or risking a circular import.
"""

from .calendar_labels import CalendarLabels
from .color import Color
from .columns import ColumnKind, ColumnWidth, Fixed, Flex
from .options import Option, Options, OptionsProvider, resolve_options
from .pct import Pct

__all__ = [
    "CalendarLabels",
    "Color",
    "ColumnKind",
    "ColumnWidth",
    "Fixed",
    "Flex",
    "Option",
    "Options",
    "OptionsProvider",
    "Pct",
    "resolve_options",
]
