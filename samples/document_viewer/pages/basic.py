"""Example: the basic viewer, one document with the standard toolbar."""

import htpy as y

# docs:start imports
import pyhx.components as c
from pyhx.components.view_model import (
    document_viewer as vm,  # Document, Mark, Note, ...
)

# docs:end imports
from pyhx.core import WebAppRouter
from samples.document_viewer.sample_document import page_url

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()


# docs:start document
# Page images of 1240 × 1754 px; the app renders them (e.g. from a PDF).
W, H = 1240, 1754

# A box is given in fractions (0–1) of the page's width and height,
# origin top left: here 8.4 % from the left, 16.4 % from the top.
NAME = vm.BoundingBox(x=0.084, y=0.164, width=0.081, height=0.025)
# docs:end document

# docs:start pixels
# OCR delivers pixels of the page image: from_pixels turns them into fractions.
BIRTH = vm.BoundingBox.from_pixels(
    x=104, y=478, width=180, height=44, page_width=W, page_height=H
)  # == vm.BoundingBox(x=0.0839, y=0.2725, width=0.1452, height=0.0251)
# docs:end pixels

# docs:start pages
registration = vm.Document(
    id="anmeldung",
    title="IV-Anmeldung 001.001",
    subtitle="Received 21.06.2026",
    pages=[
        vm.DocumentPage(
            src=page_url("anmeldung", number),
            # width=W, height=H: optional, only the aspect ratio (A4 when left out)
            annotations=[
                vm.Mark(id="name", label="Name", box=NAME),
                vm.Mark(id="birth", label="Date of birth", box=BIRTH),
            ]
            if number == 1
            else [],
        )
        for number in range(1, 13)
    ],
)
# docs:end pages


@router.page("/basic", title="Basic viewer")
async def basic() -> y.Node:
    # docs:start viewer
    # dv = c.document_viewer
    viewer = dv(id="basic", documents=[registration])[
        dv.toolbar(),  # standard controls: title, pager, zoom, fit to width
        dv.thumbnails(),
        dv.pages(),
    ]
    # docs:end viewer
    return example_page(
        title="Basic viewer",
        intro=[
            y.p[
                "A document is a list of page images; the viewer loads them as they come near and reserves each page's space from its aspect ratio. ",
                "A page's ",
                y.code["width"],
                " and ",
                y.code["height"],
                " are optional and only give that ratio: without them the viewer assumes A4 portrait and takes the real ratio from the image once it has loaded. ",
                "Marks are boxes on a page, given in fractions (0–1) of the page's width and height, so they stay in place at every zoom and image resolution. ",
                "Coordinates in pixels of the page image (e.g. from OCR) are converted with ",
                y.code["BoundingBox.from_pixels"],
                "; the viewer itself only sees fractions.",
            ],
            y.p[
                "The viewer is composed like ",
                y.code["c.card"],
                ": the root holds the documents, the parts read them. ",
                y.code["dv.toolbar()"],
                " without children shows the standard controls. Zoom, current page and scrolling stay in the browser.",
            ],
        ],
        code=code(__file__, "viewer", "document", "pixels", "pages", "imports"),
        viewer=viewer,
    )
