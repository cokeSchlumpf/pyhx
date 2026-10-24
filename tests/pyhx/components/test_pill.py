from pathlib import Path

import pytest

from pyhx.components import pill

PILL_CSS = Path("src/pyhx/static/css/pyhx/components/primitives/pill.css").read_text()


class TestPillSize:
    def test_default_size_is_md_and_variant_solid(self):
        assert 'class="hx-pill hx-pill--info hx-pill--md hx-pill--solid"' in str(
            pill("Label")
        )

    @pytest.mark.parametrize("size", ["sm", "md", "lg"])
    def test_renders_size_class(self, size):
        assert f"hx-pill--{size}" in str(pill("Label", size=size))

    @pytest.mark.parametrize("size", ["sm", "lg"])
    def test_size_has_css(self, size):
        assert f".hx-pill--{size} {{" in PILL_CSS

    def test_canvas_design_restyles_pill(self):
        assert '[data-hx-design="canvas"] .hx-pill {' in PILL_CSS


class TestPillVariant:
    def test_renders_outline_class(self):
        assert "hx-pill--outline" in str(pill("Label", variant="outline"))

    def test_outline_has_css_in_both_designs(self):
        assert ".hx-pill--outline {" in PILL_CSS
        assert '[data-hx-design="canvas"] .hx-pill--outline {' in PILL_CSS
