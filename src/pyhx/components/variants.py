"""Reusable variant types for components.

These literals enumerate the visual-variant options shared across the
component library. Components reference them in their public signatures so
the same vocabulary (appearance, variant, ...) stays consistent across the
system. Add new axes here only when they're actually shared by 2+ components.
"""

from typing import Literal

Appearance = Literal["neutral", "info", "success", "warning", "danger", "primary"]
"""Visual semantic state. Drives the color of a component."""


Variant = Literal["solid", "outline", "ghost", "link", "glass"]
"""Emphasis level. Drives whether the component is filled, outlined, transparent, rendered as a Pico-style anchor, or a semi-transparent frosted-glass fill."""


Size = Literal["sm", "md", "lg"]
"""Physical size. Drives padding, font-size, and icon scale."""

FormSize = Literal["sm", "md"]
"""Size of form fields: ``sm`` is compact (32px controls), ``md`` the full
size. Only the canvas design has a compact size; there, fields in a drawer or
in the aside of ``split_layout`` are compact unless a size says otherwise."""

LabelPosition = Literal["top", "left"]
"""Where a form field's label sits. ``left`` puts it in a column left of the
control while the field's own cell is at least 360px wide, and above the
control in a narrower cell; ``top`` keeps it above. Without a position, labels
are on top, except in a compact form of the canvas design, which puts them
left where the cell has room."""


Orientation = Literal["horizontal", "vertical"]
"""Layout axis. Drives whether a component's items flow in a row or a column."""
