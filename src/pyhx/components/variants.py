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


Orientation = Literal["horizontal", "vertical"]
"""Layout axis. Drives whether a component's items flow in a row or a column."""
