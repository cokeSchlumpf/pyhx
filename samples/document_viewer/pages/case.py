"""Example: a case page with everything together, as in the design template."""

import htpy as y

import pyhx.components as c
from pyhx.components.variants import Appearance
from pyhx.core import WebAppRouter
from samples.document_viewer.document_viewer import Mark
from samples.document_viewer.document_viewer import document_viewer as dv
from samples.document_viewer.sample_document import (
    NOTES,
    TO_CHECK,
    VALUES,
    find_document,
    medical_report,
    registration,
)

from ._layout import code, example_page

router = WebAppRouter()


def _color(color: Appearance | c.Color) -> str:
    return (
        color.value if isinstance(color, c.Color) else c.Color.appearance(color).value
    )


def _where(document_id: str, page: int) -> str:
    document = find_document(document_id)
    return f"{document.title if document else document_id}, p. {page}"


def sidebar() -> y.Node:
    return dv.sidebar(class_="sample-sidebar")[
        y.h2["Selected note"],
        y.div(
            id="sample-note-detail", class_="sample-sidebar__detail", aria_live="polite"
        )["Click a pin: its hx-get loads the note here."],
        y.h2["Notes"],
        (
            y.button(
                type="button",
                class_="sample-entry",
                aria_pressed="false",
                data_hx_document_annotation=f"case:{note.id}",
                style=f"--c: {_color(note.color)};",
            )[
                y.span[
                    y.span(class_="sample-entry__dot", aria_hidden="true"), note.label
                ],
                y.span(class_="sample-entry__where")[_where(note.document, note.page)],
                y.span(class_="sample-entry__body")[y.small[note.author], note.text],
            ]
            for note in NOTES
        ),
        y.h2["Extracted values"],
        (
            y.button(
                type="button",
                class_="sample-entry",
                aria_pressed="false",
                data_hx_document_annotation=f"case:{id_}",
            )[
                y.span[y.small[label], value],
                y.span(class_="sample-entry__where")[where],
            ]
            for id_, label, value, where in VALUES
        ),
    ]


@router.page("/case", title="Case page")
async def case() -> y.Node:
    documents = [registration(), medical_report()]
    to_check = sum(
        1
        for document in documents
        for page in document.pages
        for a in page.annotations
        if isinstance(a, Mark) and a.style in TO_CHECK
    )
    # docs:start viewer
    viewer = dv(id="case", documents=documents)[
        dv.toolbar[
            dv.back(href="/", label="Case"),
            dv.title(),  # follows the document in view
            dv.pager(),
            dv.zoom(),
            dv.fit(),
            dv.spacer(),
            c.pill(f"{to_check} to check", appearance="warning", variant="outline"),
        ],
        dv.thumbnails(),
        dv.pages(),
        sidebar(),  # dv.sidebar[...] with the app's notes and values
    ]
    # docs:end viewer
    return example_page(
        title="Case page",
        intro=y.p[
            "The case page of the design template: two documents, marks in the colours of their categories, low-confidence and contradicting values, notes of the case workers, and a sidebar with the notes (expanding while selected, loaded with hx-get from the pins) and the extracted values. ",
            "In an app this page uses ",
            y.code['CanvasShell(mode="full")'],
            " and fills the window.",
        ],
        code=code(__file__, "viewer"),
        viewer=viewer,
        height="calc(100dvh - 8rem)",
    )
