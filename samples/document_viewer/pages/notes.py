"""Example: notes as pins, their content in the sidebar, HTMX on a pin."""

import htpy as y

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer.sample_document import HEIGHT, WIDTH, page_url

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()


def at(x: int, y: int) -> vm.Point:
    return vm.Point.from_pixels(x=x, y=y, page_width=WIDTH, page_height=HEIGHT)


# docs:start notes
NOTES = {
    1: [
        vm.Note(
            id="n-address", label="Address", at=at(1100, 640)
        ),  # color="warning" (default)
    ],
    6: [
        vm.Note(
            id="n-incapacity",
            label="Start of incapacity",
            at=at(1100, 300),
            color="danger",
            # any attributes of the app on the pin: here HTMX loads the note
            attrs={"hx-get": "/sample-notes/note-au", "hx-target": "#notes-detail"},
        ),
    ],
    9: [vm.Note(id="n-employer", label="Employer", at=at(1100, 500), color="info")],
}
TEXTS = {
    "n-address": (
        "C. Morel, 24.06.2026",
        "The register of residents lists Hardstrasse 14.",
    ),
    "n-incapacity": (
        "C. Morel, 24.06.2026",
        "Handwritten: 28.04. or 23.04.? Compare with the doctor's certificate.",
    ),
    "n-employer": (
        "R. Keller, 25.06.2026",
        "Employer questionnaire sent, answer expected by 15.07.2026.",
    ),
}
# docs:end notes

document = vm.Document(
    id="anmeldung",
    title="IV-Anmeldung 001.001",
    subtitle="Received 21.06.2026",
    pages=[
        vm.DocumentPage(
            src=page_url("anmeldung", n),
            width=WIDTH,
            height=HEIGHT,
            annotations=NOTES.get(n, []),
        )
        for n in range(1, 13)
    ],
)


# docs:start entry
def note_entry(note: vm.Note, page: int) -> y.Node:
    """A sidebar entry linked to the pin; its text shows while the note is selected."""
    author, text = TEXTS[note.id]
    color = (
        note.color.value
        if isinstance(note.color, c.Color)
        else c.Color.appearance(note.color).value
    )
    return y.button(
        type="button",
        class_="sample-entry",
        aria_pressed="false",  # the viewer keeps it in step with the pin
        data_hx_document_annotation=f"notes:{note.id}",  # <viewer id>:<annotation id>
        style=f"--c: {color}",
    )[
        y.span[y.span(class_="sample-entry__dot", aria_hidden="true"), note.label],
        y.span(class_="sample-entry__where")[f"p. {page}"],
        y.span(class_="sample-entry__body")[
            y.small[author], text
        ],  # CSS: shown when pressed
    ]


# docs:end entry


# docs:start css
CSS_HINT = """
/* the app's CSS: the note's text shows only while its entry is selected */
.sample-entry__body { display: none; }
.sample-entry[aria-pressed="true"] .sample-entry__body { display: block; }
"""
# docs:end css

# docs:start event
EVENT_SCRIPT = """
document.addEventListener("hx-document:annotation-select", (event) => {
    const { viewer, id, kind } = event.detail;          // e.g. "notes", "n-address", "note"
    document.getElementById("notes-log").textContent = `${kind} ${id} selected in ${viewer}`;
});
"""
# docs:end event


@router.page("/notes", title="Notes")
async def notes() -> y.Node:
    # docs:start viewer
    viewer = dv(id="notes", documents=[document])[
        dv.toolbar(),
        dv.thumbnails(),
        dv.pages(),
        dv.sidebar(class_="sample-sidebar")[
            y.h2["Notes"],
            (note_entry(note, page) for page, notes in NOTES.items() for note in notes),
            y.h2["Loaded with hx-get"],
            y.div(id="notes-detail", class_="sample-sidebar__detail")[
                "Click the red pin on page 6."
            ],
            y.div(id="notes-log", class_="sample-sidebar__log")["click a pin"],
        ],
    ]
    # docs:end viewer
    return example_page(
        title="Notes",
        intro=[
            y.p[
                "A note is a point on a page, drawn as a pin: a dot with a lighter ring in the note's colour, the same size at any zoom. ",
                "The viewer draws only the pin; the note's content is the app's, shown beside the viewer.",
            ],
            y.ul[
                y.li[
                    "Link an entry to a pin with ",
                    y.code['data-hx-document-annotation="<viewer>:<id>"'],
                    ". Selecting either selects both: the entry gets ",
                    y.code['aria-pressed="true"'],
                    ", so CSS alone shows the note's text; selecting the entry scrolls to the pin.",
                ],
                y.li[
                    y.code["attrs"],
                    " puts the app's attributes on a pin (or a mark), e.g. ",
                    y.code["hx-get"],
                    " and ",
                    y.code["hx-target"],
                    " to load content with HTMX.",
                ],
                y.li[
                    "Every click on a pin or a mark dispatches ",
                    y.code["hx-document:annotation-select"],
                    " with the viewer, the id and the kind, for the app's own JavaScript.",
                ],
            ],
        ],
        code=code(__file__, "notes", "viewer", "entry", "css", "event"),
        viewer=viewer,
        script=EVENT_SCRIPT,
    )
