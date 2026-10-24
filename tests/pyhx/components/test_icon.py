from pathlib import Path
from typing import get_args

import pytest

from pyhx.components import button, icon, message, pill
from pyhx.components.primitives.icon import ICONS_DIR
from pyhx.core.primitives import CustomIconName, FeatherIconName

ICON_CSS = Path("src/pyhx/static/css/pyhx/components/primitives/icon.css").read_text()


class TestCustomIconNames:
    def test_every_name_has_an_svg_file_and_vice_versa(self):
        files = {path.stem for path in ICONS_DIR.glob("*.svg")}
        assert files == set(get_args(CustomIconName))

    def test_no_name_clashes_with_feather(self):
        assert not set(get_args(CustomIconName)) & set(get_args(FeatherIconName))


class TestIcon:
    def test_feather_icon_renders_placeholder(self):
        assert str(icon("check")) == '<i data-feather="check"></i>'

    def test_custom_icon_is_inlined_svg(self):
        html = str(icon("check-2"))

        assert html.startswith("<svg ")
        assert 'viewBox="0 0 20 20"' in html
        assert 'width="24" height="24"' in html
        assert 'aria-hidden="true"' in html
        assert 'class="hx-icon hx-icon-check-2"' in html
        assert '<path d="m5 10.5 3 3 7-7"/>' in html
        assert "xmlns" not in html

    def test_custom_icon_keeps_its_stroke_width(self):
        assert 'stroke-width="2.25"' in str(icon("exclamation"))

    def test_extra_attributes_and_classes_are_merged(self):
        assert 'class="hx-icon hx-icon-swap extra"' in str(icon("swap", class_="extra"))
        assert 'class="extra"' in str(icon("check", class_="extra"))

    @pytest.mark.parametrize("name", ["check", "check-2"])
    def test_circle_wraps_either_kind(self, name):
        html = str(icon(name, circle=True, appearance="success"))

        assert html.startswith(
            '<span class="hx-icon-circle hx-icon-circle--success" aria-hidden="true">'
        )

    def test_circle_defaults_to_neutral(self):
        assert "hx-icon-circle--neutral" in str(icon("exclamation", circle=True))


class TestComponentsAcceptCustomIcons:
    def test_button(self):
        assert "hx-icon-swap" in str(button("Tauschen", icon="swap"))

    def test_pill_button(self):
        assert "hx-icon-check-2" in str(pill.button(aria_label="OK", icon="check-2"))

    def test_message(self):
        assert "hx-icon-exclamation" in str(message("Text", icon="exclamation"))


class TestIconCss:
    def test_css_is_imported(self):
        pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
        assert "components/primitives/icon.css" in pyhx_css

    def test_circle_has_all_appearances(self):
        appearances = ("neutral", "primary", "info", "success", "warning", "danger")
        for appearance in appearances:
            assert f".hx-icon-circle--{appearance} {{" in ICON_CSS
