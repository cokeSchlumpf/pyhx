import asyncio
from pathlib import Path

import htpy as y
import pytest

from pyhx.components import card

CARD_CSS = Path("src/pyhx/static/css/pyhx/components/layout/card.css").read_text()


class TestCard:
    def test_renders_section_with_parts(self):
        html = str(
            card[
                card.header[
                    card.title[y.h2["Title"]],
                    card.subtle["subtle"],
                    card.subtitle["subtitle"],
                    card.actions["actions"],
                ],
                card.section[card.label["Label"], y.p["text"]],
                card.footer["footer"],
            ]
        )

        assert html == (
            '<section class="hx-card">'
            '<header class="hx-card__header">'
            '<div class="hx-card__title"><h2>Title</h2></div>'
            '<span class="hx-card__subtle">subtle</span>'
            '<p class="hx-card__subtitle">subtitle</p>'
            '<div class="hx-card__actions">actions</div>'
            "</header>"
            '<div class="hx-card__section">'
            '<div class="hx-card__label">Label</div><p>text</p>'
            "</div>"
            '<footer class="hx-card__footer">footer</footer>'
            "</section>"
        )

    def test_list_with_clickable_items(self):
        html = str(
            card.list[
                card.item[card.link(href="/doc")["Doc"]],
                card.item[card.button["Check"]],
            ]
        )

        assert html == (
            '<ul class="hx-card__list">'
            '<li class="hx-card__item"><a href="/doc" class="hx-card__link">Doc</a></li>'
            '<li class="hx-card__item">'
            '<button type="button" class="hx-card__button">Check</button>'
            "</li>"
            "</ul>"
        )

    def test_button_type_can_be_overridden(self):
        assert 'type="submit"' in str(card.button(type="submit")["Save"])

    def test_parts_pass_extra_attributes(self):
        html = str(card(id="dossier", class_="extra")[card.section(id="s")["x"]])

        assert '<section id="dossier" class="hx-card extra">' in html
        assert '<div id="s" class="hx-card__section">x</div>' in html


class TestCollapsibleCard:
    @pytest.mark.parametrize(("open", "details"), [(True, "<details open>"), (False, "<details>")])
    def test_open_makes_card_collapsible(self, open, details):
        html = str(card(open=open)[card.header["Title"], card.section["body"]])

        assert html == (
            f'<section class="hx-card">{details}'
            '<summary class="hx-card__header">Title'
            '<span class="hx-card__chevron" aria-hidden="true">'
            '<i data-feather="chevron-down"></i></span>'
            "</summary>"
            '<div class="hx-card__section">body</div>'
            "</details></section>"
        )

    def test_without_open_header_is_a_header(self):
        html = str(card[card.header["Title"]])

        assert '<header class="hx-card__header">' in html
        assert "<details" not in html

    def test_nested_card_is_not_collapsible(self):
        html = str(card(open=True)[card.header["Outer"], card[card.header["Inner"]]])

        assert '<summary class="hx-card__header">Outer' in html
        assert '<header class="hx-card__header">Inner</header>' in html

    def test_async_children_render(self):
        async def title() -> y.Node:
            return y.b["async"]

        async def render() -> str:
            node = y.div[card(open=True)[card.header[title()], card.section[title()]]]
            return "".join([chunk async for chunk in node.aiter_chunks()])

        html = asyncio.run(render())

        assert '<summary class="hx-card__header"><b>async</b>' in html
        assert '<div class="hx-card__section"><b>async</b></div>' in html


class TestCardCss:
    def test_css_is_imported(self):
        pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
        assert "components/layout/card.css" in pyhx_css

    def test_canvas_design_overrides_tokens(self):
        assert '[data-hx-design="canvas"] .hx-card {' in CARD_CSS

    def test_clickable_rows_use_stretched_overlay(self):
        assert ".hx-card__link::after" in CARD_CSS
        assert "inset: 0;" in CARD_CSS
