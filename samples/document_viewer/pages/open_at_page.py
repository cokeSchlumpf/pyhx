"""Example: one document at a time, opened at a page or a mark, with the document switcher (T-018)."""

from urllib.parse import urlencode

import htpy as y

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer.sample_document import sample_documents

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()

FOLDERS = {"anmeldung": "Registration", "arztbericht": "Medical reports"}


def _url(document: str, page: int | None = None, mark: str | None = None) -> str:
    query = {"doc": document} | ({"page": str(page)} if page else {}) | ({"mark": mark} if mark else {})
    return f"/open-at-a-page?{urlencode(query)}"


@router.page("/open-at-a-page", title="Open at a page")
async def open_at_page(doc: str = "anmeldung", page: int = 1, mark: str = "") -> y.Node:
    documents = {d.id: d for d in sample_documents()}
    document = documents.get(doc) or documents["anmeldung"]
    # docs:start viewer
    entries = [
        vm.DocumentLink(
            d.title,
            href=_url(d.id),
            group=FOLDERS[d.id],
            detail=f"{len(d.pages)} p.",
            current=d is document,
        )
        for d in documents.values()
    ] + [
        # no href: shown greyed out, can't be chosen (e.g. its pages aren't ready)
        vm.DocumentLink("Nachtrag.pdf", group="Medical reports", detail="Pages not ready")
    ]
    viewer = dv(
        id="open-at-a-page",
        documents=[document],  # one document at a time
        start=f"{document.id}:{page}",  # opens at this page …
        selected=mark or None,  # … or at this annotation, selected (wins)
    )[
        dv.toolbar[
            dv.back(href="/", label="Overview"),
            dv.files(entries),  # the current document on a button, a dropdown to switch
            dv.pager(),
            dv.zoom(),
            dv.fit(),
        ],
        dv.thumbnails(),
        dv.pages(),
    ]
    # docs:end viewer
    return example_page(
        title="Open at a page",
        intro=[
            y.p[
                "A link to a place in a document opens the viewer there: ",
                y.code["start"],
                " is a page, ",
                y.code["selected"],
                " an annotation, which is selected and scrolled into view (it wins over the page). The server renders the pager and the current thumbnail for that page, so nothing jumps from page 1.",
            ],
            y.ul[
                y.li[y.a(href=_url("anmeldung", mark="beruf"))["Registration, the occupation selected (page 9)"]],
                y.li[y.a(href=_url("arztbericht", page=2))["Medical report, page 2"]],
                y.li[y.a(href=_url("anmeldung", page=6))["Registration, page 6"]],
            ],
            y.p[
                "With many documents, show one at a time and let ",
                y.code["dv.files"],
                " switch: its button shows the current document; the dropdown below it has a search, the documents by group, and greys out those without a link. Type to filter, ↑/↓ and Enter to choose; a click outside or Esc closes it.",
            ],
        ],
        code=code(__file__, "viewer"),
        viewer=viewer,
    )
