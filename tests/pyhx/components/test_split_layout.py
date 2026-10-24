from pathlib import Path

import htpy as y

from pyhx.components import split_layout

SPLIT_CSS = Path(
    "src/pyhx/static/css/pyhx/components/layout/split-layout.css"
).read_text()


class TestSplitLayout:
    def test_renders_container_grid_and_columns(self):
        html = str(split_layout(main=y.p["main"], aside=y.p["aside"]))

        assert html == (
            '<div class="hx-split-layout"><div class="hx-split-layout__grid">'
            '<div class="hx-split-layout__main"><p>main</p></div>'
            '<aside class="hx-split-layout__aside"><p>aside</p></aside>'
            "</div></div>"
        )

    def test_passes_extra_attributes(self):
        html = str(split_layout(main="m", aside="a", class_="extra", id="dossier"))

        assert 'class="hx-split-layout extra"' in html
        assert 'id="dossier"' in html

    def test_css_is_imported(self):
        pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
        assert "components/layout/split-layout.css" in pyhx_css


class TestSplitLayoutCss:
    def test_aside_sticks_below_page_template_bars(self):
        assert "top: calc(var(--hx-sticky-top) + var(--split-layout--gap))" in SPLIT_CSS

    def test_stacks_by_container_width_not_viewport(self):
        assert "container: hx-split-layout / inline-size" in SPLIT_CSS
        assert "@container hx-split-layout (width < 58rem)" in SPLIT_CSS
        assert "@media" not in SPLIT_CSS
