import asyncio

import htpy as y
import pytest
from fastapi.testclient import TestClient

import pyhx.components as c
from pyhx.core import WebApp

dv = c.document_viewer
vm = c.document_viewer.view_model


def _doc(
    id_: str,
    *annotations: vm.Annotation,
    badge: vm.PageBadge | None = None,
    pages: int = 1,
) -> vm.Document:
    page = vm.DocumentPage(
        src="/p.png", width=10, height=10, annotations=annotations, badge=badge
    )
    return vm.Document(
        id=id_, title=id_.title(), subtitle=f"{id_} received", pages=[page] * pages
    )


def _render(*parts: y.Node, documents: list[vm.Document] | None = None) -> str:
    return str(dv(id="v", documents=documents or [_doc("a")])[parts])


class TestRoot:
    def test_renders_the_root_with_its_id(self):
        html = _render(dv.pages())

        assert 'id="v"' in html
        assert 'data-hx-document-viewer="v"' in html
        assert 'class="hx-document-viewer"' in html

    def test_passes_attributes_and_classes(self):
        html = str(
            dv(id="v", documents=[_doc("a")], class_="mine", data_x="1")[dv.pages()]
        )

        assert 'class="hx-document-viewer mine"' in html
        assert 'data-x="1"' in html

    def test_needs_a_document(self):
        with pytest.raises(ValueError):
            dv(id="v", documents=[])

    @pytest.mark.parametrize(
        "part", [dv.pages(), dv.thumbnails(), dv.pager(), dv.title()]
    )
    def test_parts_need_the_viewer(self, part: y.Node):
        with pytest.raises(RuntimeError, match="document_viewer"):
            str(y.div[part])

    def test_exposes_the_view_model(self):
        from pyhx.components.view_model import document_viewer

        assert dv.view_model is document_viewer


class TestToolbar:
    def test_without_children_shows_the_standard_controls(self):
        html = _render(dv.toolbar())

        assert 'role="toolbar"' in html
        assert "data-hx-document-title" in html
        for action in ("prev", "next", "zoom-out", "zoom-in", "fit"):
            assert f'data-hx-document-action="{action}"' in html

    def test_without_children_renders_within_the_viewer_when_async(self):
        root = dv(id="v", documents=[_doc("a")])[dv.toolbar()]

        async def render() -> str:
            return "".join([chunk async for chunk in root.aiter_chunks()])

        assert "data-hx-document-title" in asyncio.run(render())

    def test_with_children_shows_only_those_in_order(self):
        html = _render(
            dv.toolbar[
                dv.back(href="/x", label="Back"), dv.pager(), dv.spacer(), c.pill("own")
            ]
        )

        assert 'data-hx-document-action="zoom-in"' not in html
        assert html.index('href="/x"') < html.index('data-hx-document-action="prev"')
        assert html.index("hx-document-viewer__spacer") < html.index("own")

    def test_controls_are_ghost_buttons_with_names(self):
        html = _render(dv.toolbar())

        assert html.count("hx-button--ghost") == 5
        assert 'aria-label="Previous page"' in html
        assert 'aria-label="Fit to width"' in html

    def test_back_is_a_quiet_link(self):
        html = _render(dv.toolbar[dv.back(href="/case", label="Case")])

        assert '<a href="/case"' in html
        assert "hx-button--ghost" in html

    def test_title_follows_the_first_document_without_a_title(self):
        html = _render(dv.toolbar[dv.title()])

        assert "data-hx-document-title" in html
        assert ">A<" in html
        assert "a received" in html

    def test_a_fixed_title_does_not_follow(self):
        html = _render(dv.toolbar[dv.title("Fixed", "sub")])

        assert "Fixed" in html
        assert "data-hx-document-title" not in html

    def test_pager_counts_the_first_document_and_disables_previous(self):
        html = _render(dv.toolbar[dv.pager()], documents=[_doc("a", pages=3)])

        assert "data-hx-document-count" in html
        assert ">3<" in html
        assert html.count("disabled") == 1


class TestThumbnails:
    def test_one_group_per_document_with_headings_for_several(self):
        html = _render(dv.thumbnails(), documents=[_doc("a"), _doc("b")])

        assert html.count('class="hx-document-viewer__thumbnail-group"') == 2
        assert html.count("thumbnail-heading") == 2
        assert 'data-hx-document-goto="b:1"' in html

    def test_headings_follow_grouped(self):
        assert "thumbnail-heading" not in _render(dv.thumbnails())
        assert "thumbnail-heading" in _render(dv.thumbnails(grouped=True))
        assert "thumbnail-heading" not in _render(
            dv.thumbnails(grouped=False), documents=[_doc("a"), _doc("b")]
        )

    def test_the_first_page_is_current(self):
        html = _render(dv.thumbnails(), documents=[_doc("a", pages=2)])

        assert html.count('aria-current="page"') == 1

    def test_badge_only_when_the_app_gives_one(self):
        assert "__badge" not in _render(dv.thumbnails())

        badge = vm.PageBadge("3", "3 values to check", appearance="warning")
        html = _render(dv.thumbnails(), documents=[_doc("a", badge=badge)])
        assert 'data-appearance="warning"' in html
        assert 'aria-label="Page 1, 3 values to check"' in html


class TestPages:
    def test_documents_one_after_another_with_titles_for_several(self):
        html = _render(dv.pages(), documents=[_doc("a"), _doc("b", pages=2)])

        assert html.count("data-hx-document-page=") == 3
        assert html.count("hx-document-viewer__document-heading") == 2
        assert "hx-document-viewer__document-heading" not in _render(dv.pages())

    def test_first_pages_load_at_once_the_others_lazily(self):
        html = _render(dv.pages(), documents=[_doc("a", pages=4)])

        assert html.count('loading="lazy"') == 2

    def test_page_without_size_assumes_a4(self):
        page = vm.DocumentPage(src="/p.png")
        html = _render(
            dv.pages(), documents=[vm.Document(id="a", title="A", pages=[page])]
        )

        assert "aspect-ratio: 210 / 297;" in html
        assert 'data-hx-document-ratio="assumed"' in html

    def test_marks_and_notes_with_their_attributes(self):
        mark = vm.Mark(
            id="m",
            label="M",
            box=vm.BoundingBox(0.1, 0.2, 0.3, 0.1),
            style=vm.MarkStyle(color="warning", look="fill-outline"),
            attrs={"hx-get": "/m"},
        )
        note = vm.Note(
            id="n",
            label="N",
            at=vm.Point(0.5, 0.5),
            color="danger",
            attrs={"hx-get": "/n"},
        )
        html = _render(dv.pages(), documents=[_doc("a", note, mark)])

        assert 'data-look="fill-outline"' in html
        assert (
            "left: 10.0000%; top: 20.0000%; width: 30.0000%; height: 10.0000%;" in html
        )
        assert 'hx-get="/m"' in html and 'hx-get="/n"' in html
        assert 'aria-label="Note: N"' in html
        assert html.count('aria-pressed="false"') == 2
        assert html.index('data-kind="mark"') < html.index('data-kind="note"')


class TestSidebar:
    def test_holds_the_apps_content(self):
        html = _render(dv.sidebar(class_="mine")[y.p["content"]])

        assert '<aside class="hx-document-viewer__sidebar mine">' in html
        assert "content" in html


@pytest.fixture
def client() -> TestClient:
    hx = WebApp(title="Viewer")

    @hx.page("/", title="Viewer")
    async def index() -> y.Node:
        return dv(id="v", documents=[_doc("a")])[dv.toolbar(), dv.pages()]

    return TestClient(hx.create_app())


class TestAssets:
    def test_page_loads_the_script(self, client: TestClient):
        assert (
            '<script src="/static/js/pyhx.document-viewer.js"></script>'
            in client.get("/").text
        )
        assert client.get("/static/js/pyhx.document-viewer.js").status_code == 200

    def test_styles_are_imported_into_the_pyhx_layer(self, client: TestClient):
        css = client.get("/static/css/pyhx.css").text

        assert (
            '@import "./pyhx/components/layout/document-viewer.css" layer(pyhx);' in css
        )
        assert (
            client.get(
                "/static/css/pyhx/components/layout/document-viewer.css"
            ).status_code
            == 200
        )


class TestTexts:
    def test_follow_the_request_language(self, client: TestClient):
        page = client.get("/", headers={"Accept-Language": "de-CH"}).text

        assert 'aria-label="Vorherige Seite"' in page
        assert 'aria-label="An Breite anpassen"' in page
        assert 'aria-label="Seite 1"' in page
