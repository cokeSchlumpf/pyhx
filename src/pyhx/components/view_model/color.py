"""Colour value type — a hex/RGB literal or a semantic appearance token.

A :class:`Color` wraps a single string: the CSS colour value it resolves to.
That value is either a concrete literal (``"#ff00aa"`` / ``"rgb(255, 0, 170)"``)
or a ``var(--hx-color-…)`` reference the browser resolves against the active
theme. Build one via a factory rather than the token name directly:

* literal:  :meth:`Color.hex` · :meth:`Color.rgb` · :meth:`Color.rgba`
* semantic: :meth:`Color.appearance` and the per-appearance shortcuts
  (:meth:`Color.info`, :meth:`Color.danger`, :meth:`Color.primary`, …)

``str(color)`` (and ``color.value``) yields the CSS string, so a ``Color`` drops
straight into any prop or style that already takes a CSS colour.

Pure value type — no rendering and no dependency on ``data`` / ``primitives`` /
``layouts``; it only borrows the shared :data:`~pyhx.components.variants.Appearance`
vocabulary so its factories speak the same names as the components.
"""

import re
from dataclasses import dataclass

from ..variants import Appearance

_HEX_RE = re.compile(r"\A#?(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")

#: Representative scale step for an appearance — the shade the components treat
#: as the "solid" foreground colour (e.g. ``--hx-color-info-600``).
DEFAULT_SHADE = 600


@dataclass(frozen=True)
class Color:
    """A colour that resolves to a single CSS value.

    Attributes
    ----------
    value : str
        The CSS colour string — a literal (``"#ff00aa"``, ``"rgb(255, 0, 170)"``)
        or a token reference (``"var(--hx-color-info-600)"``). This is exactly
        what ``str(color)`` returns, so the colour can be handed to any CSS
        property, inline style, or component prop that expects a colour string.
    """

    value: str

    # --- literal constructors -------------------------------------------
    @classmethod
    def hex(cls, value: str) -> "Color":
        """A hex literal, e.g. ``Color.hex("#ff00aa")``.

        Accepts 3- or 6-digit hex, with or without the leading ``#``, in any
        case; normalises to lower-case 6-digit ``#rrggbb`` so equal colours
        compare equal. Raises :class:`ValueError` on a malformed value.
        """
        raw = value.strip()
        if not _HEX_RE.match(raw):
            raise ValueError(f"invalid hex colour: {value!r}")
        digits = raw.lstrip("#").lower()
        if len(digits) == 3:  # #f0a -> #ff00aa
            digits = "".join(c * 2 for c in digits)
        return cls(f"#{digits}")

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> "Color":
        """An ``rgb(r, g, b)`` literal from 0–255 channels."""
        cls._check_channels(r, g, b)
        return cls(f"rgb({r}, {g}, {b})")

    @classmethod
    def rgba(cls, r: int, g: int, b: int, a: float) -> "Color":
        """An ``rgba(r, g, b, a)`` literal — channels 0–255, alpha 0–1."""
        cls._check_channels(r, g, b)
        if not 0.0 <= a <= 1.0:
            raise ValueError(f"alpha out of range 0–1: {a}")
        return cls(f"rgba({r}, {g}, {b}, {a})")

    # --- semantic / appearance factories --------------------------------
    @classmethod
    def appearance(cls, appearance: Appearance, shade: int = DEFAULT_SHADE) -> "Color":
        """A theme token for a semantic ``appearance``.

        Resolves to ``var(--hx-color-{appearance}-{shade})`` (shade zero-padded
        to three digits, e.g. ``50`` → ``050``). ``primary`` is special-cased:
        the palette exposes only the base ``--hx-color-primary`` (no numeric
        shades), so ``shade`` is ignored for it.
        """
        if appearance == "primary":
            return cls("var(--hx-color-primary)")
        return cls(f"var(--hx-color-{appearance}-{shade:03d})")

    @classmethod
    def neutral(cls, shade: int = DEFAULT_SHADE) -> "Color":
        return cls.appearance("neutral", shade)

    @classmethod
    def info(cls, shade: int = DEFAULT_SHADE) -> "Color":
        return cls.appearance("info", shade)

    @classmethod
    def success(cls, shade: int = DEFAULT_SHADE) -> "Color":
        return cls.appearance("success", shade)

    @classmethod
    def warning(cls, shade: int = DEFAULT_SHADE) -> "Color":
        return cls.appearance("warning", shade)

    @classmethod
    def danger(cls, shade: int = DEFAULT_SHADE) -> "Color":
        return cls.appearance("danger", shade)

    @classmethod
    def primary(cls) -> "Color":
        return cls.appearance("primary")

    # --- escape hatch ---------------------------------------------------
    @classmethod
    def css(cls, value: str) -> "Color":
        """Wrap any other CSS colour value verbatim (``currentColor``, a bespoke
        ``var(--…)``, a named colour). No validation — you own the string."""
        return cls(value)

    # --- helpers --------------------------------------------------------
    @staticmethod
    def _check_channels(*channels: int) -> None:
        for c in channels:
            if not 0 <= c <= 255:
                raise ValueError(f"channel out of range 0–255: {c}")

    def __str__(self) -> str:
        return self.value
