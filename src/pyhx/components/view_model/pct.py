"""Percentage value type — a fraction constrained to ``[0, 1]``.

A :class:`Pct` wraps a single ``float`` in the closed interval ``[0, 1]`` and
guarantees that invariant at construction time: ``0.0`` is empty, ``1.0`` is
full, and anything outside the range (or ``NaN``) is rejected with
:class:`ValueError`. Build one from whichever form the caller already has:

* fraction:  ``Pct(0.5)``
* percent:   :meth:`Pct.of` — ``Pct.of(50)`` (0–100 scale)
* computed:  :meth:`Pct.clamp` — folds an out-of-range ratio into ``[0, 1]``

``str(pct)`` yields a CSS percentage (``"50%"``), so a ``Pct`` drops straight
into any prop or style that takes a CSS length/percentage, while
:attr:`Pct.value` (the fraction) and :attr:`Pct.percent` (0–100) cover the
numeric cases.

Pure value type — frozen, hashable, equality by value; no rendering and no
dependency on ``data`` / ``primitives`` / ``layouts``.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Pct:
    """A fraction constrained to the closed interval ``[0, 1]``.

    Attributes
    ----------
    value : float
        The fraction, where ``0.0`` is 0% and ``1.0`` is 100%. Values outside
        ``[0, 1]`` — and ``NaN`` — are rejected at construction.
    """

    value: float

    def __post_init__(self) -> None:
        # ``not 0.0 <= value <= 1.0`` also rejects NaN, whose comparisons are
        # all false.
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"percentage out of range 0–1: {self.value!r}")

    # --- constructors ---------------------------------------------------
    @classmethod
    def of(cls, percent: float) -> "Pct":
        """A percentage on the 0–100 scale, e.g. ``Pct.of(50)`` → ``0.5``.

        Raises :class:`ValueError` if ``percent`` falls outside ``0–100``.
        """
        return cls(percent / 100.0)

    @classmethod
    def clamp(cls, value: float) -> "Pct":
        """A fraction folded into ``[0, 1]`` — values below ``0`` become ``0``
        and values above ``1`` become ``1``.

        For computed ratios that may drift out of range (e.g. ``done / total``
        when ``done`` can exceed ``total``). ``NaN`` is still rejected.
        """
        if math.isnan(value):
            raise ValueError(f"percentage out of range 0–1: {value!r}")
        return cls(min(1.0, max(0.0, value)))

    # --- views ----------------------------------------------------------
    @property
    def percent(self) -> float:
        """The value on the 0–100 scale (``Pct(0.5).percent == 50.0``)."""
        return self.value * 100.0

    def __str__(self) -> str:
        """A CSS percentage string, e.g. ``"50%"`` (trailing zeros trimmed)."""
        return f"{self.value * 100:g}%"
