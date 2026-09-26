"""Tests for the ``Color`` value type.

`Color` wraps a single CSS colour string. Literal factories (`hex` / `rgb` /
`rgba`) validate and normalise their input; the appearance factories translate a
semantic name into a `var(--hx-color-…)` token, with `primary` special-cased to
the un-shaded base token. `str(color)` and `color.value` both yield the CSS.
"""

import pytest

from pyhx.components import Color


class TestHexLiterals:
    def test_six_digit_passthrough(self) -> None:
        assert str(Color.hex("#ff00aa")) == "#ff00aa"

    def test_three_digit_expands(self) -> None:
        assert Color.hex("#f0a").value == "#ff00aa"

    def test_normalises_case_and_missing_hash(self) -> None:
        assert Color.hex("FF00AA").value == "#ff00aa"

    @pytest.mark.parametrize("bad", ["#ff00a", "#ggghhh", "ff00aa00", "rgb(1,2,3)", ""])
    def test_rejects_malformed(self, bad: str) -> None:
        with pytest.raises(ValueError):
            Color.hex(bad)


class TestRgbLiterals:
    def test_rgb(self) -> None:
        assert str(Color.rgb(255, 0, 170)) == "rgb(255, 0, 170)"

    def test_rgba(self) -> None:
        assert str(Color.rgba(255, 0, 170, 0.5)) == "rgba(255, 0, 170, 0.5)"

    @pytest.mark.parametrize("channel", [-1, 256])
    def test_rejects_out_of_range_channel(self, channel: int) -> None:
        with pytest.raises(ValueError):
            Color.rgb(channel, 0, 0)

    @pytest.mark.parametrize("alpha", [-0.1, 1.1])
    def test_rejects_out_of_range_alpha(self, alpha: float) -> None:
        with pytest.raises(ValueError):
            Color.rgba(0, 0, 0, alpha)


class TestAppearanceTokens:
    def test_default_shade_is_600(self) -> None:
        assert str(Color.info()) == "var(--hx-color-info-600)"

    def test_shade_is_zero_padded(self) -> None:
        assert str(Color.danger(shade=50)) == "var(--hx-color-danger-050)"

    def test_primary_ignores_shade_and_has_no_scale(self) -> None:
        assert str(Color.primary()) == "var(--hx-color-primary)"

    @pytest.mark.parametrize(
        "factory, name",
        [
            (Color.neutral, "neutral"),
            (Color.info, "info"),
            (Color.success, "success"),
            (Color.warning, "warning"),
            (Color.danger, "danger"),
        ],
    )
    def test_each_appearance_maps_to_its_token(self, factory, name: str) -> None:
        assert str(factory()) == f"var(--hx-color-{name}-600)"

    def test_appearance_dispatch(self) -> None:
        assert Color.appearance("success", 100).value == "var(--hx-color-success-100)"


class TestValueSemantics:
    def test_is_frozen(self) -> None:
        with pytest.raises(Exception):
            Color.info().value = "#000000"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        assert Color.hex("#FFF") == Color.hex("#ffffff")
        assert Color.info() == Color.appearance("info")

    def test_hashable(self) -> None:
        assert len({Color.hex("#fff"), Color.hex("#ffffff"), Color.primary()}) == 2

    def test_css_escape_hatch_is_verbatim(self) -> None:
        assert Color.css("currentColor").value == "currentColor"
