"""Opening the viewer at a page, with a selected annotation, and the document switcher (T-018)."""

import re

import htpy as y

import pyhx.components as c

dv = c.document_viewer
vm = c.document_viewer.view_model


def _doc(id_: str, pages: int, *annotations: vm.Annotation) -> vm.Document:
    return vm.Document(
        id=id_,
        title=id_.title(),
        subtitle=f"{id_} received",
        pages=[
            vm.DocumentPage(
                src=f"/{id_}/{n}.png",
                width=10,
                height=14,
                annotations=annotations if n == pages else (),
            )
            for n in range(1, pages + 1)
        ],
    )


def _render(*parts: y.Node, **kwargs: str) -> str:
    return str(dv(id="v", documents=[_doc("a", 3), _doc("b", 4)], **kwargs)[parts])


def _counter(html: str) -> tuple[str, str]:
    current = re.search(r"data-hx-document-current>(\d+)<", html)
    count = re.search(r"data-hx-document-count>(\d+)<", html)
    assert current and count
    return current.group(1), count.group(1)


class TestStart:
    def test_without_start_nothing_changes(self):
        html = _render(dv.toolbar(), dv.thumbnails(), dv.pages())

        assert "data-hx-document-start" not in html
        assert "data-hx-document-selected" not in html
        assert _counter(html) == ("1", "3")
        assert 'aria-current="page" data-hx-document-goto="a:1"' in html

    def test_renders_the_start_page(self):
        html = _render(dv.toolbar(), dv.thumbnails(), dv.pages(), start="b:3")

        assert 'data-hx-document-start="b:3"' in html
        assert _counter(html) == ("3", "4")
        assert re.search(r"data-hx-document-title>B<", html)
        assert 'aria-current="page" data-hx-document-goto="b:3"' in html
        assert 'aria-current="page" data-hx-document-goto="a:1"' not in html
        # the start page and the next load at once, the others lazily
        assert '<img src="/b/3.png" alt="" width="10" height="14">' in html
        assert '<img src="/b/4.png" alt="" width="10" height="14">' in html
        assert '<img src="/a/1.png" alt="" loading="lazy"' in html

    def test_the_last_page_disables_next(self):
        html = _render(dv.pager(), start="b:4")

        buttons = re.findall(r"<button[^>]*>", html)
        previous = next(b for b in buttons if "Previous page" in b)
        following = next(b for b in buttons if "Next page" in b)
        assert "disabled" not in previous and "disabled" in following

    def test_an_unknown_start_falls_back_to_the_first_page(self):
        for start in ("x:1", "b:9", "b:0", "b", "b:two"):
            html = _render(dv.pager(), dv.thumbnails(), start=start)

            assert _counter(html) == ("1", "3")
            assert 'aria-current="page" data-hx-document-goto="a:1"' in html

    def test_renders_the_selected_annotation(self):
        mark = vm.Mark(id="m1", box=vm.BoundingBox(0.1, 0.1, 0.2, 0.1), label="Here")
        html = str(
            dv(id="v", documents=[_doc("a", 2, mark)], start="a:2", selected="m1")[
                dv.pages()
            ]
        )

        assert 'data-hx-document-selected="m1"' in html


def _entries() -> list[vm.DocumentLink]:
    return [
        vm.DocumentLink("Brief.pdf", href="/d/1", group="Letters", detail="2 p."),
        vm.DocumentLink("Befund.pdf", group="Letters", detail="Pages not ready"),
        vm.DocumentLink(
            "Röntgen.pdf", href="/d/3", group="Images", detail="6 p.", current=True
        ),
        vm.DocumentLink("Zeugnis.pdf", href="/d/4", group="Images", detail="1 p."),
    ]


class TestFiles:
    def test_shows_the_current_document_on_its_button(self):
        html = _render(dv.toolbar[dv.files(_entries())], dv.pages())

        summary = html[html.index("<summary") : html.index("</summary>")]
        assert "<strong>Röntgen.pdf</strong>" in summary
        assert "<span>Images</span>" in summary

    def test_lists_the_entries_by_group(self):
        html = _render(dv.toolbar[dv.files(_entries())], dv.pages())

        listing = html[html.index("hx-document-viewer__files-list") :]
        assert (
            listing.index("Letters")
            < listing.index("Brief.pdf")
            < listing.index("Images")
        )
        assert html.count('class="hx-document-viewer__files-group"') == 2
        assert '<a href="/d/1" class="hx-document-viewer__files-entry"' in html
        assert (
            'aria-current="true" data-hx-document-search="rontgen.pdf images"' in html
        )
        # an entry without a link is greyed out and not a link
        assert re.search(
            r'<span class="hx-document-viewer__files-entry" aria-disabled="true"'
            r' data-hx-document-search="befund.pdf letters">',
            html,
        )
        assert "Pages not ready" in html
        assert 'type="search"' in html and "data-hx-document-files-search" in html
        assert 'data-template="{n} of 4 match">4 of 4 match<' in html

    def test_links_the_neighbouring_documents(self):
        html = _render(dv.toolbar[dv.files(_entries())], dv.pages())

        assert re.search(r'<a[^>]*href="/d/1"[^>]*aria-label="Previous document"', html)
        assert re.search(r'<a[^>]*href="/d/4"[^>]*aria-label="Next document"', html)
        assert "3 of 4 documents" in html

    def test_skips_entries_without_a_link_and_ends_disabled(self):
        entries = _entries()
        entries[0] = vm.DocumentLink(
            "Brief.pdf", href="/d/1", group="Letters", current=True
        )
        entries[2] = vm.DocumentLink("Röntgen.pdf", href="/d/3", group="Images")
        html = _render(dv.toolbar[dv.files(entries)], dv.pages())

        assert re.search(
            r'aria-label="Previous document"[^>]*disabled|disabled[^>]*aria-label="Previous document"',
            html,
        )
        assert re.search(r'<a[^>]*href="/d/3"[^>]*aria-label="Next document"', html)
        assert "1 of 4 documents" in html

    def test_needs_the_viewer(self):
        import pytest

        with pytest.raises(RuntimeError, match="document_viewer"):
            str(y.div[dv.files(_entries())])
