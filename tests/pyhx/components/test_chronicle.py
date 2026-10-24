from pathlib import Path

import htpy as y

from pyhx.components import chronicle

CHRONICLE_CSS = Path(
    "src/pyhx/static/css/pyhx/components/primitives/chronicle.css"
).read_text()


class TestChronicle:
    def test_renders_list_with_entry_columns(self):
        html = str(
            chronicle[
                chronicle.entry(date="12.04.2026")[
                    chronicle.title["Title"],
                    chronicle.text["Text"],
                ]
            ]
        )

        assert html == (
            '<ol class="hx-chronicle">'
            '<li class="hx-chronicle__entry">'
            '<span class="hx-chronicle__date">12.04.2026</span>'
            '<span class="hx-chronicle__marker" aria-hidden="true">'
            '<span class="hx-chronicle__dot hx-chronicle__dot--neutral"></span>'
            "</span>"
            '<div class="hx-chronicle__content">'
            '<div class="hx-chronicle__title">Title</div>'
            '<p class="hx-chronicle__text">Text</p>'
            "</div>"
            "</li>"
            "</ol>"
        )

    def test_appearance_colours_the_dot(self):
        assert "hx-chronicle__dot--success" in str(
            chronicle.entry(appearance="success")["x"]
        )

    def test_color_sets_custom_property_and_modifier(self):
        html = str(chronicle.entry(color="#F194B4")["x"])

        assert 'style="--chronicle--color: #F194B4"' in html
        assert 'class="hx-chronicle__entry hx-chronicle__entry--colored"' in html

    def test_without_color_no_style(self):
        assert "style=" not in str(chronicle.entry()["x"])

    def test_icon_replaces_the_dot(self):
        html = str(chronicle.entry(icon="check-2", appearance="success")["x"])

        assert "hx-chronicle__dot" not in html
        assert 'class="hx-icon-circle hx-icon-circle--success"' in html
        assert "hx-icon-check-2" in html

    def test_list_and_entry_pass_extra_attributes(self):
        html = str(chronicle(id="docs")[chronicle.entry(id="e1")["x"]])

        assert '<ol id="docs" class="hx-chronicle">' in html
        assert '<li id="e1" class="hx-chronicle__entry">' in html

    def test_title_link_is_kept(self):
        html = str(chronicle.title[y.a(href="/doc")["Doc"]])

        assert '<a href="/doc">Doc</a>' in html


class TestChronicleCss:
    def test_css_is_imported(self):
        pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
        assert "components/primitives/chronicle.css" in pyhx_css

    def test_icons_widen_the_marker_column_for_all_entries(self):
        assert ".hx-chronicle:has(.hx-icon-circle) {" in CHRONICLE_CSS

    def test_free_colour_wins_over_appearance(self):
        assert ".hx-chronicle__entry--colored .hx-chronicle__dot {" in CHRONICLE_CSS
        assert ".hx-chronicle__entry--colored .hx-icon-circle {" in CHRONICLE_CSS

    def test_title_link_stretches_across_entry(self):
        assert ".hx-chronicle__title a::after {" in CHRONICLE_CSS
