"""Example: the source picker in a dialog, the posted choice shown on the page (T-021).

Three dialogs: one sample document, the two sample documents in one picker,
and 30 documents in three folders, one at a time with the document switcher
(``files``). The pages keep their marks but not their notes: pins only
distract while choosing a source.
"""

from dataclasses import replace
from typing import Annotated

import htpy as y
from fastapi import Query, Request

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer import sample_document

from ._layout import code, example_page

router = WebAppRouter()


def _marks_only(document: vm.Document) -> vm.Document:
    pages = [
        replace(page, annotations=[a for a in page.annotations if isinstance(a, vm.Mark)])
        for page in document.pages
    ]
    return replace(document, pages=pages)


def sample_documents() -> list[vm.Document]:
    return [_marks_only(d) for d in sample_document.sample_documents()]


def registration() -> vm.Document:
    return _marks_only(sample_document.registration())


def medical_report() -> vm.Document:
    return _marks_only(sample_document.medical_report())

RESULT_ID = "source-picker-result"

# shows the picker's event in the dialog, so the sample can be followed without devtools
_SCRIPT = """
document.addEventListener("hx-source-picker:change", (event) => {
    const log = document.getElementById("source-picker-log");
    if (log) log.textContent = "hx-source-picker:change " + JSON.stringify(event.detail);
});
"""


def _box(text: str) -> vm.BoundingBox | None:
    parts = [float(p) for p in text.split(",")] if text else []
    return vm.BoundingBox(*parts) if len(parts) == 4 else None


def _many() -> dict[str, vm.Document]:
    """30 made-up documents in three folders, built from the pages of the two sample documents."""
    folders = [
        ("Applications", "Application {n:02d}.pdf", registration(), 6),
        ("Medical reports", "Medical report {n:02d}.pdf", medical_report(), 12),
        ("Correspondence", "Letter {n:02d}.pdf", medical_report(), 12),
    ]
    documents: dict[str, vm.Document] = {}
    for folder, title, source, count in folders:
        for n in range(1, count + 1):
            id_ = f"{folder[:3].lower()}-{n:02d}"
            documents[id_] = vm.Document(id=id_, title=title.format(n=n), subtitle=folder, pages=source.pages)
    return documents


MANY = _many()


# docs:start dialog
@router.fragment.get("/source-picker/dialog")
async def source_dialog(
    document: Annotated[str, Query()] = "",
    page: Annotated[int, Query()] = 1,
    box: Annotated[str, Query()] = "",
) -> y.Node:
    # editing a source: open the picker at its page, with its area
    value = vm.SourceChoice(document, page, _box(box)) if document else None
    return c.dialog_content(
        c.source_picker(
            id="source-picker",
            documents=sample_documents(),
            name="source",  # inputs source_document, source_page, source_box
            value=value,
        ),
        y.small(id="source-picker-log", class_="sample-source__log"),
        title="Add source",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url()),
            c.button("Use source", appearance="primary", hx_post=use_source.url()),
        ],
    )


@router.fragment.post("/source-picker/use")
async def use_source(request: Request) -> y.Node:
    form = await request.form()
    choice = vm.SourceChoice.from_form(form, name="source")  # ValueError if malformed
    return y.fragment[
        c.dialog_content(),
        _result(choice, dict(form)),
    ]
# docs:end dialog


# docs:start many
def _many_picker(document_id: str, value: vm.SourceChoice | None = None) -> y.Node:
    document = MANY.get(document_id) or next(iter(MANY.values()))
    files = [
        vm.DocumentLink(
            d.title,
            # fetched with htmx; the answer replaces the picker, the dialog stays
            href=f"{many_picker.url()}?document={d.id}",
            group=d.subtitle,
            detail=f"{len(d.pages)} p.",
            current=d is document,
        )
        for d in MANY.values()
    ]
    return c.source_picker(
        id="source-picker",
        documents=[document],  # only the current one
        files=files,  # the document switcher in the toolbar
        value=value,
    )


@router.fragment.get("/source-picker/many/picker")
async def many_picker(document: Annotated[str, Query()] = "") -> y.Node:
    return _many_picker(document)


@router.fragment.get("/source-picker/many")
async def many_dialog(
    document: Annotated[str, Query()] = "",
    page: Annotated[int, Query()] = 1,
    box: Annotated[str, Query()] = "",
) -> y.Node:
    value = vm.SourceChoice(document, page, _box(box)) if document else None
    return c.dialog_content(
        _many_picker(document, value),
        y.small(id="source-picker-log", class_="sample-source__log"),
        title="Add source",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url()),
            c.button("Use source", appearance="primary", hx_post=use_source.url()),
        ],
    )
# docs:end many


# docs:start single
@router.fragment.get("/source-picker/single")
async def single_dialog() -> y.Node:
    return c.dialog_content(
        # one document: the title in the toolbar, no switcher
        c.source_picker(id="source-picker", documents=[medical_report()]),
        y.small(id="source-picker-log", class_="sample-source__log"),
        title="Add source",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url()),
            c.button("Use source", appearance="primary", hx_post=use_source.url()),
        ],
    )
# docs:end single


def _result(choice: vm.SourceChoice | None, posted: dict[str, object] | None = None) -> y.Node:
    documents = {d.id: d for d in sample_documents()} | MANY
    if choice is None:
        body: y.Node = y.p["Nothing chosen yet."]
    else:
        title = documents[choice.document_id].title if choice.document_id in documents else choice.document_id
        where = "the whole page" if choice.box is None else f"the area {choice.box_value}"
        query = f"document={choice.document_id}&page={choice.page}&box={choice.box_value}"
        body = [
            y.p[y.strong[f"{title}, page {choice.page}"], f": {where}."],
            y.pre[y.code["\n".join(f"{k} = {v!r}" for k, v in (posted or {}).items())]],
            c.button(
                "Edit this source",
                icon="edit-2",
                **c.open_dialog_htmx_attributes(
                    f"{(many_dialog if choice.document_id in MANY else source_dialog).url()}?{query}"
                ),
            ),
        ]
    return y.div(id=RESULT_ID, class_="sample-source__result", hx_swap_oob="true")[body]


@router.page("/source-picker", title="Source picker")
async def source_picker_page() -> y.Node:
    return example_page(
        title="Source picker",
        intro=[
            y.p[
                y.code["c.source_picker"],
                " lets the user choose where something comes from: a document, a page, and optionally an area on it. It shows one page at a time; thumbnails and the pager choose the page. Drag on the page to draw an area, drag it or its corners to change it; Escape or “Clear area” removes it. Without an area the whole page is the choice.",
            ],
            y.p[
                "The choice is in hidden inputs (",
                y.code["source_document"],
                ", ",
                y.code["source_page"],
                ", ",
                y.code["source_box"],
                "), so the dialog's action posts it; ",
                y.code["SourceChoice.from_form"],
                " reads it back.",
            ],
            y.p[
                "With many documents, give ",
                y.code["files"],
                ": the picker shows one document, and the toolbar the document switcher of ",
                y.code["dv.files"],
                " (search, folders, previous and next). Choosing a document fetches its entry's link with htmx and replaces the picker, so the dialog stays open.",
            ],
            y.p(style="display: flex; flex-wrap: wrap; gap: 0.5rem;")[
                c.button("Add source", appearance="primary", **c.open_dialog_htmx_attributes(source_dialog.url())),
                c.button("Add source (one document)", **c.open_dialog_htmx_attributes(single_dialog.url())),
                c.button("Add source (30 documents)", **c.open_dialog_htmx_attributes(many_dialog.url())),
            ],
        ],
        code=code(__file__, "dialog", "single", "many"),
        viewer=_result(None),
        height="auto",
        script=_SCRIPT,
    )
