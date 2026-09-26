"""Tests for the ``Pct`` value type.

`Pct` wraps a single ``float`` fraction constrained to the closed interval
`[0, 1]`; the invariant is enforced at construction. `Pct.of` builds one from
the 0–100 scale, `Pct.clamp` folds an out-of-range ratio into the interval.
`str(pct)` yields a CSS percentage and `pct.value` / `pct.percent` cover the
numeric forms.
"""

import math

import pytest

from pyhx.components import Pct


class TestConstruction:
    def test_fraction_passthrough(self) -> None:
        assert Pct(0.5).value == 0.5

    @pytest.mark.parametrize("bound", [0.0, 1.0])
    def test_bounds_are_inclusive(self, bound: float) -> None:
        assert Pct(bound).value == bound

    @pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -1.0, math.nan])
    def test_rejects_out_of_range(self, bad: float) -> None:
        with pytest.raises(ValueError):
            Pct(bad)


class TestOf:
    def test_percent_scale(self) -> None:
        assert Pct.of(50).value == 0.5

    @pytest.mark.parametrize("bound", [0, 100])
    def test_bounds_are_inclusive(self, bound: float) -> None:
        Pct.of(bound)  # does not raise

    @pytest.mark.parametrize("bad", [-1, 101])
    def test_rejects_out_of_range(self, bad: float) -> None:
        with pytest.raises(ValueError):
            Pct.of(bad)


class TestClamp:
    def test_below_floor_becomes_zero(self) -> None:
        assert Pct.clamp(-0.5).value == 0.0

    def test_above_ceiling_becomes_one(self) -> None:
        assert Pct.clamp(1.5).value == 1.0

    def test_in_range_passthrough(self) -> None:
        assert Pct.clamp(0.25).value == 0.25

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValueError):
            Pct.clamp(math.nan)


class TestViews:
    def test_percent_property(self) -> None:
        assert Pct(0.5).percent == 50.0

    @pytest.mark.parametrize(
        "value, expected",
        [(0.5, "50%"), (0.0, "0%"), (1.0, "100%"), (0.125, "12.5%")],
    )
    def test_str_is_css_percentage(self, value: float, expected: str) -> None:
        assert str(Pct(value)) == expected


class TestValueSemantics:
    def test_is_frozen(self) -> None:
        with pytest.raises(Exception):
            Pct(0.5).value = 0.6  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        assert Pct(0.5) == Pct.of(50)

    def test_hashable(self) -> None:
        assert len({Pct(0.5), Pct.of(50), Pct(1.0)}) == 2
