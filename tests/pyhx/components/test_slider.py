"""Tests for the slider primitive.

Covers the complete control (scale, step snapping, per-thumb bounds, hidden
inputs, validation) and the hand-composable visual elements. Rendering does
not require an application route or request context.
"""

import re

import pytest

from pyhx.components import Pct, SliderThumb, form_field, slider


def _hidden_values(html: str, name: str) -> list[str]:
    return re.findall(rf'<input type="hidden" name="{name}" value="([^"]*)"', html)


def _thumbs(html: str) -> list[str]:
    return re.findall(r'<span role="slider"[^>]*>', html)


# --- complete control -------------------------------------------------------


def test_slider_defaults_to_single_thumb_at_scale_start() -> None:
    html = str(slider("volume"))

    assert len(_thumbs(html)) == 1
    assert _hidden_values(html, "volume") == ["0"]
    assert 'data-slider-min="0"' in html
    assert 'data-slider-max="100"' in html
    assert 'data-slider-step="1"' in html


def test_slider_single_value_fills_range_from_start() -> None:
    html = str(slider("volume", value=40))

    assert _hidden_values(html, "volume") == ["40"]
    assert "--hx-slider--start: 0%; --hx-slider--end: 40%" in html
    assert "--hx-slider--position: 40%" in html


def test_slider_positions_values_on_own_scale() -> None:
    html = str(slider("period", value=(2022, 2026), min=2020, max=2030))

    assert _hidden_values(html, "period") == ["2022", "2026"]
    assert "--hx-slider--start: 20%; --hx-slider--end: 60%" in html


def test_slider_three_thumbs_render_no_range() -> None:
    html = str(slider("stops", value=(0, 50, 100)))

    assert len(_thumbs(html)) == 3
    assert "hx-slider__range" not in html


def test_slider_snaps_values_to_step_from_min() -> None:
    html = str(slider("s", value=(13, 17), min=1, max=21, step=5))

    assert _hidden_values(html, "s") == ["11", "16"]


def test_slider_fractional_step_has_no_float_noise() -> None:
    html = str(slider("ratio", value=0.3, min=0, max=1, step=0.1))

    assert _hidden_values(html, "ratio") == ["0.3"]


def test_slider_clamps_value_to_thumb_bounds() -> None:
    html = str(slider("s", value=SliderThumb(90, max=60)))

    assert _hidden_values(html, "s") == ["60"]


def test_slider_thumb_reports_own_bounds_and_neighbour_aware_aria() -> None:
    html = str(
        slider(
            "stops",
            value=[
                SliderThumb(0, max=30, label="Start"),
                SliderThumb(50, min=20, max=80, label="Middle"),
                SliderThumb(100, min=70, label="End"),
            ],
        )
    )
    start, middle, end = _thumbs(html)

    assert 'aria-label="Start"' in start
    assert 'data-slider-min="0"' in start and 'data-slider-max="30"' in start
    assert 'aria-valuemin="0"' in start and 'aria-valuemax="50"' in start
    assert 'data-slider-min="20"' in middle and 'data-slider-max="80"' in middle
    assert 'aria-valuemin="0"' in middle and 'aria-valuemax="100"' in middle
    assert 'aria-valuemin="50"' in end and 'aria-valuemax="100"' in end


def test_slider_links_thumbs_and_inputs_by_index() -> None:
    html = str(slider("p", value=(10, 20)))

    assert html.count('data-slider-index="0"') == 2
    assert html.count('data-slider-index="1"') == 2


def test_slider_disabled_keeps_inputs_submitting() -> None:
    html = str(slider("locked", value=(20, 60), disabled=True))

    assert 'aria-disabled="true"' in html
    assert all('tabindex="-1"' in t for t in _thumbs(html))
    assert "disabled" not in re.sub(r'aria-disabled="true"', "", html)
    assert _hidden_values(html, "locked") == ["20", "60"]


def test_slider_works_as_form_field_input() -> None:
    html = str(form_field("period", "Period", slider, error_text="Required"))

    assert _hidden_values(html, "period") == ["0"]
    assert 'aria-invalid="true"' in html


@pytest.mark.parametrize(
    ("value", "kwargs"),
    [
        (None, {"min": 10, "max": 10}),
        (None, {"step": 0}),
        ((60, 40), {}),
        (SliderThumb(5, min=-10), {}),
        (SliderThumb(5, min=50, max=40), {}),
        ([], {}),
    ],
    ids=[
        "empty-scale",
        "zero-step",
        "descending",
        "bounds-outside-scale",
        "empty-bounds",
        "no-values",
    ],
)
def test_slider_rejects_invalid_configuration(value, kwargs) -> None:
    with pytest.raises(ValueError):
        slider("s", value=value, **kwargs)


# --- elements ---------------------------------------------------------------


def test_slider_container_renders_root_with_children() -> None:
    html = str(slider.container(id="zoom")[slider.track])

    assert 'class="hx-slider"' in html
    assert 'id="zoom"' in html
    assert 'class="hx-slider__track"' in html


def test_slider_range_defaults_to_full_track() -> None:
    html = str(slider.range())

    assert "--hx-slider--start: 0%" in html
    assert "--hx-slider--end: 100%" in html


def test_slider_thumb_defaults_aria_to_percent_scale() -> None:
    html = str(slider.thumb(Pct.of(40), aria_label="Start"))

    assert "--hx-slider--position: 40%" in html
    assert 'role="slider"' in html
    assert 'aria-label="Start"' in html
    assert 'aria-valuenow="40"' in html


def test_slider_thumb_merges_existing_style() -> None:
    html = str(slider.thumb(Pct.of(10), style="color: red"))

    assert "color: red" in html
    assert "--hx-slider--position: 10%" in html
