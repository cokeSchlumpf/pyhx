from pathlib import Path

import htpy as y

from pyhx.components import meta

META_CSS = Path("src/pyhx/static/css/pyhx/components/primitives/meta.css").read_text()


class TestMeta:
    def test_renders_items_separated_by_spaces(self):
        assert str(meta("Eingang 15.03.2026", "12 Seiten")) == (
            '<span class="hx-meta">'
            '<span class="hx-meta__item">Eingang 15.03.2026</span> '
            '<span class="hx-meta__item">12 Seiten</span>'
            "</span>"
        )

    def test_single_item(self):
        assert str(meta("only")) == (
            '<span class="hx-meta"><span class="hx-meta__item">only</span></span>'
        )

    def test_item_can_hold_nodes(self):
        html = str(meta(["Fall ", y.strong["IV-2026-0142"]]))

        assert (
            '<span class="hx-meta__item">Fall <strong>IV-2026-0142</strong></span>'
            in html
        )

    def test_passes_extra_attributes(self):
        assert '<span id="m" class="hx-meta extra">' in str(
            meta("a", id="m", class_="extra")
        )


class TestMetaCss:
    def test_css_is_imported(self):
        pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
        assert "components/primitives/meta.css" in pyhx_css

    def test_separator_is_hidden_from_screen_readers(self):
        assert 'content: "·" / "";' in META_CSS

    def test_separator_follows_all_but_the_last_item(self):
        assert ".hx-meta__item:not(:last-child)::after" in META_CSS
