"""Tests for the generic metric-tile component.

The tests verify its semantic structure, appearance modifier, optional
supporting text, and forwarding of additional HTML attributes. Rendering does
not require an application route or request context.
"""

from pyhx.components import metric_tile


def test_metric_tile_renders_value_and_label() -> None:
    html = str(
        metric_tile(
            value="92%",
            label="Evidence coverage",
        )
    )

    assert "<dl" in html
    assert "<dt" in html
    assert "<dd" in html
    assert "92%" in html
    assert "Evidence coverage" in html
    assert "hx-metric-tile--neutral" in html


def test_metric_tile_renders_appearance() -> None:
    html = str(
        metric_tile(
            value="7",
            label="Open questions",
            appearance="warning",
        )
    )

    assert "hx-metric-tile--warning" in html


def test_metric_tile_renders_optional_supporting_text() -> None:
    html = str(
        metric_tile(
            value="7",
            label="Open questions",
            supporting_text="Across all stages",
        )
    )

    assert "hx-metric-tile__supporting-text" in html
    assert "Across all stages" in html


def test_metric_tile_omits_missing_supporting_text() -> None:
    html = str(
        metric_tile(
            value="92%",
            label="Evidence coverage",
        )
    )

    assert "hx-metric-tile__supporting-text" not in html


def test_metric_tile_forwards_html_attributes() -> None:
    html = str(
        metric_tile(
            value="92%",
            label="Evidence coverage",
            id="evidence-coverage",
            aria_label="Evidence coverage: 92%",
        )
    )

    assert 'id="evidence-coverage"' in html
    assert 'aria-label="Evidence coverage: 92%"' in html