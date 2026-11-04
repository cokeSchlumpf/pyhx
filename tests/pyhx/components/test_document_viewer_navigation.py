"""T-022: annotations of several marks, categories and the annotation pager."""

import htpy as y
import pytest

import pyhx.components as c

dv = c.document_viewer
vm = c.document_viewer.view_model

BOX = vm.BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05)


def _mark(id_: str, **kwargs) -> vm.Mark:
    return vm.Mark(id=id_, box=BOX, label=id_, **kwargs)


def _render(
    *annotations: vm.Annotation, parts: tuple[y.Node, ...] = (), **kwargs
) -> str:
    page = vm.DocumentPage(src="/p.png", width=10, height=10, annotations=annotations)
    document = vm.Document(id="d", title="D", pages=[page])
    return str(dv(id="v", documents=[document], **kwargs)[dv.pages(), *parts])


class TestAnnotationOfSeveralMarks:
    def test_marks_of_one_annotation_share_its_id(self):
        html = _render(_mark("m1", annotation="a"), _mark("m2", annotation="a"))

        assert html.count('data-hx-document-annotation-id="a"') == 2
        assert "m1" not in html.replace('aria-label="m1"', "").replace('title="m1"', "")

    def test_a_mark_without_annotation_is_its_own(self):
        mark = _mark("m1")

        assert mark.annotation_id == "m1"
        assert 'data-hx-document-annotation-id="m1"' in _render(mark)

    def test_markup_without_the_new_parameters_is_unchanged(self):
        html = _render(_mark("m1"), vm.Note(id="n1", at=vm.Point(0.5, 0.5), label="N"))

        assert "data-hx-document-category" not in html
        assert "data-hx-document-hidden" not in html
        assert " hidden" not in html


class TestCategories:
    def test_marks_and_notes_carry_their_category(self):
        html = _render(
            _mark("m1", category="diagnosis"),
            vm.Note(id="n1", at=vm.Point(0.5, 0.5), label="N", category="note"),
        )

        assert 'data-hx-document-category="diagnosis"' in html
        assert 'data-hx-document-category="note"' in html

    def test_hidden_categories_are_rendered_hidden(self):
        html = _render(
            _mark("m1", category="a"),
            _mark("m2", category="b"),
            vm.Note(id="n1", at=vm.Point(0.5, 0.5), label="N", category="b"),
            hidden_categories=["b"],
        )

        assert 'data-hx-document-hidden="b"' in html
        assert html.count("hidden") - html.count("data-hx-document-hidden") == 2

    @pytest.mark.parametrize("category", ["", "two words", "tab\there"])
    def test_categories_have_no_whitespace(self, category: str):
        with pytest.raises(ValueError, match="category"):
            _mark("m1", category=category)
        with pytest.raises(ValueError, match="category"):
            vm.Note(id="n", at=vm.Point(0.5, 0.5), label="N", category=category)
        with pytest.raises(ValueError, match="category"):
            dv(
                id="v",
                documents=[vm.Document(id="d", title="D", pages=[])],
                hidden_categories=[category],
            )


class TestAnnotationPager:
    def test_counts_shown_annotations_once(self):
        html = _render(
            _mark("m1", annotation="a", category="x"),
            _mark("m2", annotation="a", category="x"),
            _mark("m3", category="x"),
            _mark("m4", category="y"),
            vm.Note(id="n1", at=vm.Point(0.5, 0.5), label="N"),
            parts=(dv.annotation_pager(),),
            hidden_categories=["y"],
        )

        assert "data-hx-document-annotation-position" in html
        assert "– / 3" in html
        assert 'data-hx-document-action="annotation-prev"' in html
        assert 'data-hx-document-action="annotation-next"' in html
        assert 'aria-label="Previous annotation"' in html
        assert 'aria-label="Next annotation"' in html

    def test_takes_the_apps_labels(self):
        html = _render(
            _mark("m1"),
            parts=(
                dv.annotation_pager(
                    previous_label="Previous finding", next_label="Next finding"
                ),
            ),
        )

        assert 'aria-label="Previous finding"' in html
        assert 'aria-label="Next finding"' in html

    def test_is_disabled_without_annotations(self):
        html = _render(parts=(dv.annotation_pager(),))

        assert "– / 0" in html
        assert html.count("disabled") == 2

    def test_needs_the_viewer(self):
        with pytest.raises(RuntimeError, match="annotation_pager"):
            str(y.div[dv.annotation_pager()])


def test_category_query_names_the_url_parameter():
    html = _render(_mark("m1", category="a"), category_query="types")

    assert 'data-hx-document-category-query="types"' in html
    assert "data-hx-document-category-query" not in _render(_mark("m1"))
