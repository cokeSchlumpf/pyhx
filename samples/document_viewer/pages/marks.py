"""Example: marks in colours and looks, the selected mark and its spotlight."""

import dataclasses

import htpy as y

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer import sample_document as data

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()

# docs:start styles
# The app maps its own categories and its confidence to colours and looks.
PERSON = vm.MarkStyle(color=c.Color.hex("#0f766e"))  # look="fill" (default)
ADDRESS = vm.MarkStyle(color=c.Color.hex("#1d4ed8"))
WORK = vm.MarkStyle(color=c.Color.hex("#6d28d9"))
UNCERTAIN = vm.MarkStyle(
    color="warning", look="fill-outline"
)  # read with low confidence
CONTEXT = vm.MarkStyle(color="neutral", look="outline")  # only context
# docs:end styles

KINDS: list[tuple[str, str, vm.MarkStyle]] = [
    ("person", "Person", PERSON),
    ("address", "Address", ADDRESS),
    ("work", "Employment", WORK),
    ("uncertain", "Low confidence", UNCERTAIN),
    ("context", "Context", CONTEXT),
]


def _marks_only(document: vm.Document) -> vm.Document:
    """The registration without its notes: this example is about marks."""
    pages = [
        dataclasses.replace(
            page, annotations=[a for a in page.annotations if isinstance(a, vm.Mark)]
        )
        for page in document.pages
    ]
    return dataclasses.replace(document, pages=pages)


def _ids(document: vm.Document, style: vm.MarkStyle) -> list[str]:
    return [
        a.id
        for page in document.pages
        for a in page.annotations
        if isinstance(a, vm.Mark) and a.style == style
    ]


def _color(style: vm.MarkStyle) -> str:
    color = style.color
    return (
        color.value if isinstance(color, c.Color) else c.Color.appearance(color).value
    )


# docs:start sidebar
def kind_row(key: str, name: str, style: vm.MarkStyle, ids: list[str]) -> y.Node:
    """All marks of a kind are shown; the steps select one instance after the other."""
    return y.div(class_="sample-kind", data_kind=key, data_ids=" ".join(ids))[
        y.span[
            y.span(
                class_="sample-kind__swatch",
                data_look=style.look,
                style=f"--c: {_color(style)}",
            ),
            name,
        ],
        y.span(class_="sample-kind__step")[
            c.button(
                icon="chevron-left",
                variant="ghost",
                size="sm",
                type="button",
                aria_label=f"Previous: {name}",
                data_step="-1",
            ),
            y.span(data_position=True)[f"– / {len(ids)}"],
            c.button(
                icon="chevron-right",
                variant="ghost",
                size="sm",
                type="button",
                aria_label=f"Next: {name}",
                data_step="1",
            ),
        ],
    ]


# docs:end sidebar


# docs:start script
STEP_SCRIPT = """
document.addEventListener("click", (event) => {
    const step = event.target.closest("[data-step]");
    if (!step) return;
    const row = step.closest("[data-ids]");
    const ids = row.dataset.ids.split(" ");
    const index = (Number(row.dataset.index ?? -1) + Number(step.dataset.step) + ids.length) % ids.length;
    row.dataset.index = index;
    row.querySelector("[data-position]").textContent = `${index + 1} / ${ids.length}`;
    pyhx.documentViewer("marks").activate(ids[index]);   // scroll into view and select
});
"""
# docs:end script


@router.page("/marks", title="Marks")
async def marks() -> y.Node:
    document = _marks_only(data.registration())
    # docs:start viewer
    viewer = dv(id="marks", documents=[document])[
        dv.toolbar(),
        dv.thumbnails(),
        dv.pages(),
        dv.sidebar(class_="sample-sidebar")[
            y.h2["Marks by kind"],
            (
                kind_row(key, name, style, _ids(document, style))
                for key, name, style in KINDS
            ),
        ],
    ]
    # docs:end viewer
    return example_page(
        title="Marks",
        intro=[
            y.p[
                "A mark highlights an area like a text marker: the tint blends into the page, so the text below keeps its contrast. ",
                "Its style is a colour (an ",
                y.code["Appearance"],
                " or any ",
                y.code["Color"],
                ") and a look: ",
                y.code["fill"],
                ", ",
                y.code["outline"],
                " or ",
                y.code["fill-outline"],
                ". pyhx draws hover and selected for every style; the app maps its categories and confidence to styles.",
            ],
            y.p[
                "All marks of a kind stay visible. Step through the instances of a kind in the sidebar: the selected one gets a border and a ring, and the other marks recede until the selection is cleared (click it again, or Esc). ",
                "The steps use the viewer's JavaScript API ",
                y.code['pyhx.documentViewer("marks").activate(id)'],
                "; a click on a mark selects it as well.",
            ],
        ],
        code=code(__file__, "styles", "viewer", "sidebar", "script"),
        viewer=viewer,
        script=STEP_SCRIPT,
    )
