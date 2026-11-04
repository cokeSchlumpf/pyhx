import re

import pytest

import pyhx.components as c

vm = c.document_viewer.view_model


def _documents() -> list[vm.Document]:
    mark = vm.Mark(id="m1", box=vm.BoundingBox(0.1, 0.1, 0.2, 0.1), label="Name")
    return [
        vm.Document(
            id="letter",
            title="Letter",
            pages=[vm.DocumentPage(src="/l1.png", width=10, height=14)],
        ),
        vm.Document(
            id="report",
            title="Report",
            pages=[
                vm.DocumentPage(src="/r1.png"),
                vm.DocumentPage(src="/r2.png", annotations=[mark]),
            ],
        ),
    ]


def _render(**kwargs) -> str:
    return str(c.source_picker(id="pick", documents=_documents(), **kwargs))


def _input(html: str, name: str) -> str:
    match = re.search(rf'<input type="hidden" name="{name}" value="([^"]*)">', html)
    assert match, name
    return match.group(1)


def _shown_pages(html: str) -> list[str]:
    pages = re.findall(r'<section class="hx-document-viewer__page"[^>]*>', html)
    return [
        re.search(r'data-hx-document-page="([^"]+)"', p).group(1)  # type: ignore[union-attr]
        for p in pages
        if " hidden" not in p
    ]


class TestRendering:
    def test_without_value_the_first_page_is_chosen_whole(self):
        html = _render()

        assert _input(html, "source_document") == "letter"
        assert _input(html, "source_page") == "1"
        assert _input(html, "source_box") == ""
        assert _shown_pages(html) == ["letter:1"]
        assert "Letter, page 1: whole page" in html
        assert re.search(r"<button[^>]*disabled[^>]*data-hx-source-picker-clear", html)

    def test_is_a_paged_document_viewer_with_its_parts(self):
        html = _render()

        assert 'data-hx-document-viewer="pick"' in html
        assert "data-hx-document-paged" in html
        assert 'data-hx-source-picker="source"' in html
        assert 'class="hx-document-viewer hx-source-picker"' in html
        assert 'class="hx-document-viewer__thumbnails"' in html
        assert 'data-hx-document-action="fit"' in html
        assert 'aria-label="Fit page"' in html

    def test_a_value_opens_at_its_page_with_its_box(self):
        value = vm.SourceChoice("report", 2, vm.BoundingBox(0.1, 0.2, 0.3, 0.4))

        html = _render(name="src", value=value)

        assert _input(html, "src_document") == "report"
        assert _input(html, "src_page") == "2"
        assert _input(html, "src_box") == "0.1000,0.2000,0.3000,0.4000"
        assert _shown_pages(html) == ["report:2"]
        assert 'data-hx-document-start="report:2"' in html
        assert "Report, page 2: marked area" in html
        assert not re.search(r"<button[^>]*disabled[^>]*data-hx-source-picker-clear", html)

    @pytest.mark.parametrize(
        "value", [vm.SourceChoice("other", 1), vm.SourceChoice("report", 3)]
    )
    def test_an_unknown_value_falls_back_to_the_first_page(self, value):
        html = _render(value=value)

        assert _input(html, "source_document") == "letter"
        assert _input(html, "source_page") == "1"
        assert _input(html, "source_box") == ""

    def test_annotations_are_read_only(self):
        html = _render()

        assert '<div class="hx-document-viewer__annotations" inert>' in html
        assert 'aria-label="Name"' in html

    def test_the_footer_carries_the_texts_for_the_script(self):
        html = _render()

        assert 'data-text-whole="{document}, page {page}: whole page"' in html
        assert 'data-text-area="{document}, page {page}: marked area"' in html
        assert 'data-text-area-label="Marked area"' in html

    def test_without_files_the_toolbar_has_the_title(self):
        html = _render()

        assert "hx-document-viewer__title" in html
        assert "hx-document-viewer__files" not in html

    def test_files_put_the_document_switcher_in_place_of_the_title(self):
        files = [
            vm.DocumentLink("Letter", href="/pick?d=letter", group="Mail", current=True),
            vm.DocumentLink("Report", href="/pick?d=report", group="Reports"),
        ]

        html = str(c.source_picker(id="pick", documents=_documents()[:1], files=files))

        assert "hx-document-viewer__title" not in html
        assert 'class="hx-document-viewer__files-menu"' in html
        assert 'href="/pick?d=report"' in html
        assert "1 of 2 documents" in html
        assert _input(html, "source_document") == "letter"

    def test_a_single_document_without_files(self):
        html = str(c.source_picker(id="pick", documents=_documents()[1:]))

        assert "hx-document-viewer__title" in html
        assert "hx-document-viewer__files" not in html
        assert _input(html, "source_document") == "report"
        assert _shown_pages(html) == ["report:1"]

    def test_files_with_a_single_entry_look_like_a_single_document(self):
        files = [vm.DocumentLink("Report", href="/pick?d=report", current=True)]

        with_files = str(c.source_picker(id="pick", documents=_documents()[1:], files=files))
        without = str(c.source_picker(id="pick", documents=_documents()[1:]))

        assert with_files == without

    def test_needs_a_document(self):
        with pytest.raises(ValueError):
            c.source_picker(id="pick", documents=[])

    def test_a_document_viewer_is_unchanged(self):
        html = str(c.document_viewer(id="v", documents=_documents())[c.document_viewer.pages()])

        assert "data-hx-document-paged" not in html
        assert " hidden" not in html
        assert "inert" not in html


class TestSourceChoiceFromForm:
    def test_reads_page_and_box(self):
        form = {"s_document": "report", "s_page": "2", "s_box": "0.1,0.2,0.3,0.4"}

        choice = vm.SourceChoice.from_form(form, name="s")

        assert choice == vm.SourceChoice("report", 2, vm.BoundingBox(0.1, 0.2, 0.3, 0.4))

    def test_an_empty_box_is_the_whole_page(self):
        form = {"source_document": "letter", "source_page": "1", "source_box": ""}

        assert vm.SourceChoice.from_form(form) == vm.SourceChoice("letter", 1)

    def test_no_document_is_none(self):
        assert vm.SourceChoice.from_form({}) is None
        assert vm.SourceChoice.from_form({"source_document": ""}) is None

    def test_a_rounding_step_beyond_the_edge_is_taken_back(self):
        form = {"source_document": "a", "source_page": "1", "source_box": "0.3334,0.5,0.6667,0.5001"}

        choice = vm.SourceChoice.from_form(form)

        assert choice is not None and choice.box is not None
        assert choice.box.x + choice.box.width == pytest.approx(1)
        assert choice.box.y + choice.box.height == pytest.approx(1)

    @pytest.mark.parametrize(
        ("page", "box"),
        [
            ("0", ""),
            ("x", ""),
            ("", ""),
            ("-1", ""),
            ("1", "0.1,0.2,0.3"),
            ("1", "a,b,c,d"),
            ("1", "0.5,0.5,0.6,0.1"),
            ("1", "nan,0,0.1,0.1"),
            ("1", "-0.1,0,0.1,0.1"),
        ],
    )
    def test_malformed_input_raises(self, page: str, box: str):
        form = {"source_document": "a", "source_page": page, "source_box": box}

        with pytest.raises(ValueError):
            vm.SourceChoice.from_form(form)

    def test_box_value_has_four_decimals(self):
        choice = vm.SourceChoice("a", 1, vm.BoundingBox(0.12346, 0.5, 0.25, 0.125))

        assert choice.box_value == "0.1235,0.5000,0.2500,0.1250"
        assert vm.SourceChoice("a", 1).box_value == ""
