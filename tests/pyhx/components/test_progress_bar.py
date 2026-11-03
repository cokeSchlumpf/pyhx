"""Tests for the progress bar: modes, motions, semantics, texts, variants."""

from pathlib import Path

import htpy as y
import pytest

import pyhx
from pyhx.components import progress_bar
from pyhx.components.view_model import Pct


def _html(node: y.Node) -> str:
    return str(node)


class TestValue:
    def test_fill_covers_the_value(self) -> None:
        html = _html(progress_bar(Pct(0.35)))

        assert 'style="--progress-bar--value: 35%"' in html

    def test_track_is_a_progressbar_with_its_value_in_percent(self) -> None:
        html = _html(progress_bar(Pct(0.666)))

        assert 'role="progressbar"' in html
        assert 'aria-valuemin="0"' in html
        assert 'aria-valuemax="100"' in html
        assert 'aria-valuenow="67"' in html

    def test_value_text_is_announced_when_it_is_a_string(self) -> None:
        html = _html(progress_bar(Pct(0.7), value_text="7 of 10 files"))

        assert 'aria-valuetext="7 of 10 files"' in html


class TestModes:
    def test_static_by_default(self) -> None:
        html = _html(progress_bar(Pct(0.5)))

        assert "hx-progress-bar--working" not in html
        assert "hx-progress-bar--sheen" not in html
        assert "aria-busy" not in html

    @pytest.mark.parametrize("motion", ["sheen", "stripes", "pulse"])
    def test_working_moves_as_chosen(self, motion) -> None:
        html = _html(progress_bar(Pct(0.5), working=True, motion=motion))

        assert "hx-progress-bar--working" in html
        assert f"hx-progress-bar--{motion}" in html
        assert 'aria-busy="true"' in html

    def test_working_moves_with_the_sheen_by_default(self) -> None:
        assert "hx-progress-bar--sheen" in _html(progress_bar(Pct(0.5), working=True))

    def test_waiting_without_a_value(self) -> None:
        html = _html(progress_bar(None, working=True, label="Waiting"))

        assert "hx-progress-bar--waiting" in html
        assert "hx-progress-bar--working" not in html
        assert "aria-valuenow" not in html
        assert "--progress-bar--value" not in html
        assert 'aria-busy="true"' in html


class TestTexts:
    def test_bar_alone_without_texts(self) -> None:
        html = _html(progress_bar(Pct(0.5)))

        assert "hx-progress-bar__head" not in html
        assert "hx-progress-bar__supporting-text" not in html

    def test_label_value_and_supporting_text(self) -> None:
        html = _html(
            progress_bar(
                Pct(0.35),
                label="Analysing",
                value_text="35 %",
                supporting_text="Page 4 of 12",
            )
        )

        assert '<span class="hx-progress-bar__label">Analysing</span>' in html
        assert '<span class="hx-progress-bar__value">35 %</span>' in html
        assert (
            '<div class="hx-progress-bar__supporting-text">Page 4 of 12</div>' in html
        )
        assert html.index("__head") < html.index("__track") < html.index("__supporting")

    def test_label_is_the_accessible_name(self) -> None:
        assert 'aria-label="Analysing"' in _html(
            progress_bar(Pct(0.1), label="Analysing")
        )

    def test_aria_label_wins_over_the_label(self) -> None:
        html = _html(
            progress_bar(Pct(0.1), label=y.strong["Analysing"], aria_label="Analysis")
        )

        assert 'aria-label="Analysis"' in html

    def test_no_accessible_name_from_a_node(self) -> None:
        assert "aria-label" not in _html(progress_bar(Pct(0.1), label=y.strong["x"]))


class TestVariants:
    def test_defaults(self) -> None:
        html = _html(progress_bar(Pct(0.5)))

        assert "hx-progress-bar--primary" in html
        assert "hx-progress-bar--md" in html

    def test_appearance_and_size(self) -> None:
        html = _html(progress_bar(Pct(1.0), appearance="success", size="sm"))

        assert "hx-progress-bar--success" in html
        assert "hx-progress-bar--sm" in html

    def test_kwargs_reach_the_root(self) -> None:
        html = _html(progress_bar(Pct(0.5), id="job-1", class_="extra"))

        assert 'id="job-1"' in html
        assert 'class="hx-progress-bar hx-progress-bar--primary' in html
        assert "extra" in html


def test_styles_stop_the_motion_for_reduced_motion() -> None:
    css = (
        Path(pyhx.__file__).parent
        / "static/css/pyhx/components/primitives/progress-bar.css"
    ).read_text()

    assert "@media (prefers-reduced-motion: reduce)" in css
    assert (
        "progress-bar.css"
        in (Path(pyhx.__file__).parent / "static/css/pyhx.css").read_text()
    )
