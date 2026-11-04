"""Example: the source picker in a dialog, the posted choice shown on the page (T-021)."""

from typing import Annotated

import htpy as y
from fastapi import Query, Request

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer.sample_document import sample_documents

from ._layout import code, example_page

router = WebAppRouter()

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


def _result(choice: vm.SourceChoice | None, posted: dict[str, object] | None = None) -> y.Node:
    documents = {d.id: d for d in sample_documents()}
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
                **c.open_dialog_htmx_attributes(f"{source_dialog.url()}?{query}"),
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
                " reads it back. ",
                c.button("Add source", appearance="primary", **c.open_dialog_htmx_attributes(source_dialog.url())),
            ],
        ],
        code=code(__file__, "dialog"),
        viewer=_result(None),
        height="auto",
        script=_SCRIPT,
    )
