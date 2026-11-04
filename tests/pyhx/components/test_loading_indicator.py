"""Tests for the loading indicator: semantics, kinds, variants, CSS rules."""

from pathlib import Path

import pytest

import pyhx
from pyhx.components import loading_indicator

_KINDS = ("spinner", "ripple", "pulse", "dots", "bars")

_CSS_DIR = Path(pyhx.__file__).parent / "static/css"


def _css() -> str:
    return (_CSS_DIR / "pyhx/components/primitives/loading-indicator.css").read_text()


def _rule(selector: str, css: str | None = None) -> str:
    """The declarations of the last rule for ``selector`` in ``css``."""
    css = _css() if css is None else css
    start = css.rindex(f"\n{selector} {{") + len(selector) + 3
    return css[start : css.index("}", start)]


def _reduced_motion() -> str:
    css = _css()
    return css[css.index("@media (prefers-reduced-motion: reduce)") :]


class TestSemantics:
    def test_status_named_by_its_label(self) -> None:
        html = str(loading_indicator(label="Saving"))

        assert html.startswith("<span ")
        assert 'role="status"' in html
        assert 'aria-label="Saving"' in html

    def test_no_visible_text(self) -> None:
        html = str(loading_indicator(label="Saving", kind="dots"))

        assert ">Saving<" not in html

    @pytest.mark.parametrize("kind", _KINDS)
    def test_never_busy(self, kind) -> None:
        # Pico draws its own spinner before every `[aria-busy=true]` element.
        assert "aria-busy" not in str(loading_indicator(label="x", kind=kind))

    def test_label_is_required(self) -> None:
        with pytest.raises(TypeError):
            loading_indicator()  # type: ignore[call-arg]

    def test_attributes_reach_the_root(self) -> None:
        html = str(loading_indicator(label="x", id="job-1", class_="extra"))

        assert 'id="job-1"' in html
        assert "extra" in html


class TestVariants:
    def test_defaults(self) -> None:
        html = str(loading_indicator(label="x"))

        assert "hx-loading-indicator--spinner" in html
        assert "hx-loading-indicator--primary" in html
        assert "hx-loading-indicator--md" in html

    @pytest.mark.parametrize("kind", _KINDS)
    def test_kind(self, kind) -> None:
        assert f"hx-loading-indicator--{kind}" in str(
            loading_indicator(label="x", kind=kind)
        )

    @pytest.mark.parametrize(
        ("kind", "parts"),
        [("spinner", 0), ("ripple", 0), ("pulse", 0), ("dots", 3), ("bars", 3)],
    )
    def test_dots_and_bars_have_three_parts(self, kind, parts) -> None:
        html = str(loading_indicator(label="x", kind=kind))

        assert html.count("hx-loading-indicator__part") == parts

    @pytest.mark.parametrize(
        "appearance", ["neutral", "primary", "info", "success", "warning", "danger"]
    )
    def test_appearance(self, appearance) -> None:
        html = str(loading_indicator(label="x", appearance=appearance))

        assert f"hx-loading-indicator--{appearance}" in html
        assert f".hx-loading-indicator--{appearance} {{" in _css()

    @pytest.mark.parametrize("size", ["sm", "md", "lg"])
    def test_size(self, size) -> None:
        assert f"hx-loading-indicator--{size}" in str(
            loading_indicator(label="x", size=size)
        )


class TestStyles:
    def test_styles_are_loaded(self) -> None:
        assert "loading-indicator.css" in (_CSS_DIR / "pyhx.css").read_text()

    def test_centred_on_its_line(self) -> None:
        rule = _rule(".hx-loading-indicator")

        assert "align-items: center;" in rule
        assert (
            "vertical-align: calc(0.5cap - var(--loading-indicator--height) / 2);"
            in rule
        )

    @pytest.mark.parametrize(
        "selector",
        [
            ".hx-loading-indicator--pulse",
            ".hx-loading-indicator--ripple::after",
            ".hx-loading-indicator--spinner",
            ".hx-loading-indicator--dots .hx-loading-indicator__part",
            ".hx-loading-indicator--bars .hx-loading-indicator__part",
        ],
    )
    def test_every_kind_moves(self, selector) -> None:
        assert "animation: hx-loading-indicator-" in _rule(selector)

    def test_reduced_motion_stops_every_animation(self) -> None:
        rule = _rule(
            "    .hx-loading-indicator,\n"
            "    .hx-loading-indicator .hx-loading-indicator__part",
            _reduced_motion(),
        )

        assert "animation: none;" in rule

    @pytest.mark.parametrize(
        ("selector", "declaration"),
        [
            ("    .hx-loading-indicator--ripple::after", "display: none;"),
            ("    .hx-loading-indicator--spinner", "border-right-color: currentColor;"),
            (
                "    .hx-loading-indicator--dots .hx-loading-indicator__part",
                "opacity: 0.6;",
            ),
            (
                "    .hx-loading-indicator--bars .hx-loading-indicator__part",
                "transform: scaleY(0.6);",
            ),
        ],
    )
    def test_reduced_motion_keeps_the_mark_visible(self, selector, declaration) -> None:
        assert declaration in _rule(selector, _reduced_motion())

    def test_spinner_ring_follows_the_mark_colour(self) -> None:
        assert "var(--loading-indicator--track)" in _rule(
            ".hx-loading-indicator--spinner"
        )
        assert "color-mix(in srgb, currentColor" in _rule(".hx-loading-indicator")

    def test_takes_the_text_colour_of_a_solid_button(self) -> None:
        rule = _rule(".hx-button--solid .hx-loading-indicator")

        assert "--loading-indicator--color: currentColor;" in rule
        # Last in the file, so it wins over the canvas design's appearances.
        css = _css()
        assert css.rindex(".hx-button--solid .hx-loading-indicator") > css.rindex(
            '[data-hx-design="canvas"]'
        )

    def test_canvas_primary_is_the_text_colour(self) -> None:
        assert "var(--hx-color-text)" in _rule(
            '[data-hx-design="canvas"] .hx-loading-indicator--primary'
        )


def _keyframes(name: str) -> str:
    css = _css()
    block = css[css.index(f"@keyframes {name} ") :]
    return block[: block.index("\n}") + 2]


class TestMotionStaysInsideTheBox:
    """Nothing paints outside the mark's box, so the gap next to it counts."""

    def test_ripple_box_holds_its_ring(self) -> None:
        rule = _rule(".hx-loading-indicator--ripple")

        assert "width: var(--loading-indicator--box);" in rule
        assert "height: var(--loading-indicator--box);" in rule
        # The ring starts at the dot (half the box) and grows to twice it.
        assert "transform: scale(2);" in _keyframes("hx-loading-indicator-ripple")

    def test_ripple_dot_and_ring_are_centred(self) -> None:
        rule = _rule(
            ".hx-loading-indicator--ripple::before,\n"
            ".hx-loading-indicator--ripple::after"
        )

        assert "top: 50%;" in rule
        assert "left: 50%;" in rule
        assert "width: var(--loading-indicator--dot);" in rule

    def test_pulse_only_shrinks(self) -> None:
        keyframes = _keyframes("hx-loading-indicator-pulse")

        assert "scale(1)" in keyframes
        assert "scale(0.8)" in keyframes

    def test_bars_never_grow_beyond_their_height(self) -> None:
        keyframes = _keyframes("hx-loading-indicator-bar")

        assert "scaleY(1)" in keyframes
        assert "scaleY(0.35)" in keyframes
