import htpy as y
import pytest
from fastapi.testclient import TestClient

import pyhx.components as c
from samples.document_viewer.main import app

dv = c.document_viewer
vm = c.document_viewer.view_model

EXAMPLES = [
    "/basic",
    "/documents",
    "/marks",
    "/notes",
    "/toolbar",
    "/case",
    "/annotation-list",
]


def _doc(id_: str, *annotations, badge: vm.PageBadge | None = None) -> vm.Document:
    page = vm.DocumentPage(
        src="/p.png", width=10, height=10, annotations=annotations, badge=badge
    )
    return vm.Document(id=id_, title=id_.title(), pages=[page])


def _render(*parts: y.Node, documents: list[vm.Document] | None = None) -> str:
    return str(dv(id="v", documents=documents or [_doc("a")])[parts])


class TestExamplePages:
    def test_the_overview_links_every_example(self):
        html = TestClient(app).get("/").text

        for path in EXAMPLES:
            assert f'href="{path}"' in html

    @pytest.mark.parametrize("path", EXAMPLES)
    def test_each_example_shows_code_and_a_viewer(self, path: str):
        html = TestClient(app).get(path).text

        assert "data-hx-document-viewer=" in html
        assert "hx-code" in html
        assert "docs:start" not in html

    def test_several_documents_have_groups_and_badges(self):
        html = TestClient(app).get("/documents").text

        assert html.count('class="hx-document-viewer__thumbnail-group"') == 2
        assert html.count("data-hx-document-page=") == 15
        assert 'aria-label="Page 6, 2 values, 2 to check"' in html

    def test_notes_link_entries_and_carry_attrs(self):
        html = TestClient(app).get("/notes").text

        assert 'aria-label="Note: Address"' in html
        assert 'data-hx-document-annotation="notes:n-address"' in html
        assert 'hx-get="/sample-notes/note-au"' in html

    def test_serves_page_images_and_notes(self):
        client = TestClient(app)

        assert client.get("/sample-pages/anmeldung/9.svg").status_code == 200
        assert client.get("/sample-pages/arztbericht/4.svg").status_code == 404
        assert "hard to read" in client.get("/sample-notes/note-au").text
        assert client.get("/sample-notes/unknown").status_code == 404


class TestComposition:
    def test_toolbar_without_children_has_the_standard_controls(self):
        html = _render(dv.toolbar())

        assert "data-hx-document-title" in html
        assert 'data-hx-document-action="prev"' in html
        assert 'data-hx-document-action="zoom-in"' in html
        assert 'data-hx-document-action="fit"' in html

    def test_toolbar_with_children_shows_only_those(self):
        html = _render(
            dv.toolbar[dv.back(href="/x", label="Back"), dv.pager(), c.pill("own")]
        )

        assert 'href="/x"' in html
        assert 'data-hx-document-action="prev"' in html
        assert 'data-hx-document-action="zoom-in"' not in html
        assert "own" in html

    def test_a_fixed_title_does_not_follow(self):
        html = _render(dv.toolbar[dv.title("Fixed")])

        assert "Fixed" in html
        assert "data-hx-document-title" not in html

    def test_groups_have_headings_with_several_documents_or_when_asked(self):
        one = [_doc("a")]
        two = [_doc("a"), _doc("b")]

        assert "thumbnail-heading" not in _render(dv.thumbnails(), documents=one)
        assert "thumbnail-heading" in _render(
            dv.thumbnails(grouped=True), documents=one
        )
        assert _render(dv.thumbnails(), documents=two).count("thumbnail-heading") == 2
        assert "thumbnail-heading" not in _render(
            dv.thumbnails(grouped=False), documents=two
        )

    def test_badge_only_when_the_app_gives_one(self):
        badge = vm.PageBadge("3", "3 values", appearance="warning")

        assert "__badge" not in _render(dv.thumbnails())
        html = _render(dv.thumbnails(), documents=[_doc("a", badge=badge)])
        assert 'data-appearance="warning"' in html
        assert 'aria-label="Page 1, 3 values"' in html

    def test_marks_and_notes_with_their_attributes(self):
        mark = vm.Mark(
            id="m",
            label="M",
            box=vm.BoundingBox(0.1, 0.1, 0.2, 0.1),
            attrs={"hx-get": "/m"},
        )
        note = vm.Note(
            id="n",
            label="N",
            at=vm.Point(0.5, 0.5),
            color="danger",
            attrs={"hx-get": "/n"},
        )
        html = _render(dv.pages(), documents=[_doc("a", mark, note)])

        assert 'data-kind="mark"' in html
        assert 'hx-get="/m"' in html
        assert 'aria-label="Note: N"' in html
        assert 'hx-get="/n"' in html
        assert html.index('data-kind="mark"') < html.index('data-kind="note"')

    def test_sidebar_holds_the_apps_content(self):
        html = _render(dv.sidebar[y.p["mine"]])

        assert 'class="hx-document-viewer__sidebar' in html
        assert "mine" in html

    def test_parts_need_the_viewer(self):
        with pytest.raises(RuntimeError):
            str(y.div[dv.pages()])

    def test_needs_a_document(self):
        with pytest.raises(ValueError):
            dv(id="v", documents=[])


class TestPageSize:
    def test_a_page_with_a_size_has_its_ratio(self):
        page = vm.DocumentPage(src="/p.png", width=1240, height=1754)
        html = _render(
            dv.pages(), documents=[vm.Document(id="a", title="A", pages=[page])]
        )

        assert "aspect-ratio: 1240 / 1754;" in html
        assert "data-hx-document-ratio" not in html

    @pytest.mark.parametrize("size", [{}, {"width": 1240}, {"height": 1754}])
    def test_without_both_sizes_a4_is_assumed(self, size: dict[str, int]):
        page = vm.DocumentPage(src="/p.png", **size)
        html = _render(
            dv.pages(), documents=[vm.Document(id="a", title="A", pages=[page])]
        )

        assert "aspect-ratio: 210 / 297;" in html
        assert 'data-hx-document-ratio="assumed"' in html

    def test_refuses_a_size_that_is_not_positive(self):
        with pytest.raises(ValueError):
            vm.DocumentPage(src="/p.png", width=0, height=10)


class TestGeometry:
    def test_box_from_pixels_gives_fractions_of_the_page(self):
        box = vm.BoundingBox.from_pixels(
            x=124, y=175.4, width=620, height=87.7, page_width=1240, page_height=1754
        )

        assert (box.x, box.y, box.width, box.height) == pytest.approx(
            (0.1, 0.1, 0.5, 0.05)
        )

    def test_refuses_a_box_outside_the_page(self):
        with pytest.raises(ValueError):
            vm.BoundingBox(x=0.8, y=0.1, width=0.3, height=0.1)

    def test_point_from_pixels(self):
        point = vm.Point.from_pixels(x=620, y=877, page_width=1240, page_height=1754)

        assert point == vm.Point(0.5, 0.5)


class TestAnnotationList:
    def test_lists_annotations_with_toggles_and_the_pager(self):
        html = TestClient(app).get("/annotation-list").text

        assert 'data-hx-document-category-toggle="list:remark"' in html
        assert 'data-hx-document-category="list:remark"' in html
        assert 'data-hx-document-hidden="check"' in html
        assert "data-hx-document-annotation-position" in html
        # the remark over two lines and the one over two pages: two marks each, one entry each
        assert html.count('data-hx-document-annotation-id="r1"') == 2
        assert html.count('data-hx-document-annotation-id="r2"') == 2
        assert html.count('data-hx-document-annotation="list:r1"') == 1
        assert html.count('data-hx-document-annotation="list:r2"') == 1
        assert 'data-hx-document-categories-show="list"' in html
        assert 'data-hx-document-categories-hide="list"' in html

    def test_reads_the_shown_categories_from_the_url(self):
        html = TestClient(app).get("/annotation-list?types=person,check").text

        assert 'data-hx-document-category-query="types"' in html
        assert 'data-hx-document-hidden="address health remark work"' in html
