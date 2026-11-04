"""Example: a list of the annotations beside the viewer, by category, with previous and next."""

import dataclasses
from collections import Counter

import htpy as y

import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm
from pyhx.core import WebAppRouter
from samples.document_viewer import sample_document as data

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()

VIEWER = "list"

CATEGORIES: dict[str, tuple[str, str]] = {
    "person": ("Person", "#0f766e"),
    "address": ("Address", "#1d4ed8"),
    "work": ("Employment", "#6d28d9"),
    "health": ("Health", "#0369a1"),
    "check": ("To check", "#b45309"),
    "remark": ("Remarks", "#be185d"),
}
STYLE_CATEGORY = {
    data.PERSON: "person",
    data.ADDRESS: "address",
    data.WORK: "work",
    data.UNCERTAIN: "check",
    data.CONTRADICTION: "check",
    data.HEALTH: "health",
    data.CONTEXT: "remark",
}


def _bar(y_px: int, width: int) -> vm.BoundingBox:
    """A filler line of the sample's page images (grey bars every 44 px)."""
    return vm.BoundingBox.from_pixels(
        x=96,
        y=y_px - 6,
        width=width + 8,
        height=26,
        page_width=data.WIDTH,
        page_height=data.HEIGHT,
    )


# docs:start annotations
REMARK = vm.MarkStyle(color=c.Color.hex("#be185d"))

# One annotation over two lines (page 2) and one over two pages (3 and 4):
# its marks share ``annotation``, so they are selected and stepped through as one.
REMARKS: dict[int, list[vm.Mark]] = {
    2: [
        vm.Mark(
            id="r1-a",
            annotation="r1",
            label="Remark over two lines",
            box=_bar(410, 1040),
            style=REMARK,
            category="remark",
        ),
        vm.Mark(
            id="r1-b",
            annotation="r1",
            label="Remark over two lines",
            box=_bar(454, 960),
            style=REMARK,
            category="remark",
        ),
    ],
    3: [
        vm.Mark(
            id="r2-a",
            annotation="r2",
            label="Remark over two pages",
            box=_bar(1540, 1040),
            style=REMARK,
            category="remark",
        )
    ],
    4: [
        vm.Mark(
            id="r2-b",
            annotation="r2",
            label="Remark over two pages",
            box=_bar(220, 1040),
            style=REMARK,
            category="remark",
        )
    ],
}


def with_categories(document: vm.Document) -> vm.Document:
    """The registration's marks with a category each, plus the remarks; no notes."""
    pages = []
    for number, page in enumerate(document.pages, start=1):
        marks = [
            dataclasses.replace(a, category=STYLE_CATEGORY[a.style])
            for a in page.annotations
            if isinstance(a, vm.Mark)
        ]
        pages.append(
            dataclasses.replace(page, annotations=[*marks, *REMARKS.get(number, [])])
        )
    return dataclasses.replace(document, pages=pages)


# docs:end annotations


def _entries(document: vm.Document) -> dict[str, list[tuple[str, str, int]]]:
    """``category -> [(annotation id, label, page)]``, each annotation once, in page order."""
    seen: set[str] = set()
    entries: dict[str, list[tuple[str, str, int]]] = {key: [] for key in CATEGORIES}
    for number, page in enumerate(document.pages, start=1):
        for a in page.annotations:
            if isinstance(a, vm.Mark) and a.category and a.annotation_id not in seen:
                seen.add(a.annotation_id)
                entries[a.category].append((a.annotation_id, a.label, number))
    return entries


# docs:start sidebar
def toggle(key: str, count: int) -> y.Node:
    """Shows and hides a category; pyhx keeps ``aria-pressed`` up to date."""
    name, color = CATEGORIES[key]
    return y.button(
        type="button",
        class_="sample-toggle",
        style=f"--c: {color}",
        aria_pressed="true",
        data_hx_document_category_toggle=f"{VIEWER}:{key}",
    )[y.span(class_="sample-entry__dot"), name, y.small[str(count)]]


def group(key: str, entries: list[tuple[str, str, int]]) -> y.Node:
    """The entries of a category; hidden with it (``data-hx-document-category``)."""
    name, color = CATEGORIES[key]
    return y.section(
        data_hx_document_category=f"{VIEWER}:{key}", style=f"--c: {color}"
    )[
        y.h2[name],
        (
            y.button(
                type="button",
                class_="sample-entry",
                aria_pressed="false",
                data_hx_document_annotation=f"{VIEWER}:{id_}",
            )[
                y.span[y.span(class_="sample-entry__dot"), label],
                y.span(class_="sample-entry__where")[f"p. {page}"],
            ]
            for id_, label, page in entries
        ),
    ]


# docs:end sidebar


@router.page("/annotation-list", title="Annotation list")
async def annotation_list(types: str | None = None) -> y.Node:
    document = with_categories(data.registration())
    entries = _entries(document)
    counts = Counter({key: len(items) for key, items in entries.items()})
    # docs:start viewer
    # ?types= holds the shown categories (written by the viewer); "To check" starts hidden
    shown = set(types.split(",")) if types is not None else set(CATEGORIES) - {"check"}
    viewer = dv(
        id=VIEWER,
        documents=[document],
        hidden_categories=[key for key in CATEGORIES if key not in shown],
        category_query="types",
    )[
        dv.toolbar(),
        dv.thumbnails(),
        dv.pages(),
        dv.sidebar(class_="sample-sidebar")[
            y.div(class_="sample-toggles")[
                (toggle(key, counts[key]) for key in CATEGORIES)
            ],
            y.div(class_="sample-pager")[dv.annotation_pager()],
            (group(key, items) for key, items in entries.items() if items),
        ],
    ]
    # docs:end viewer
    return example_page(
        title="Annotation list",
        intro=[
            y.p[
                "The app lists the annotations beside the viewer, grouped by category. ",
                "Marks with the same ",
                y.code["annotation"],
                " are one annotation: the remark over two lines on page 2 and the one from page 3 to page 4 are selected, highlighted and stepped through as one.",
            ],
            y.p[
                y.code["dv.annotation_pager()"],
                " steps through the shown annotations in document order. The toggles (",
                y.code["data-hx-document-category-toggle"],
                ") show and hide a category in the browser, its marks and the entries marked with ",
                y.code["data-hx-document-category"],
                "; “To check” starts hidden (",
                y.code["hidden_categories"],
                "). A click on a mark scrolls its entry into view in the sidebar.",
            ],
        ],
        code=code(__file__, "annotations", "sidebar", "viewer"),
        viewer=viewer,
    )
