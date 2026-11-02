"""Example: a toolbar composed of the viewer's controls and the app's own."""

import htpy as y

import pyhx.components as c
from pyhx.core import WebAppRouter
from samples.document_viewer.sample_document import registration

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()


@router.page("/toolbar", title="Custom toolbar")
async def toolbar() -> y.Node:
    # docs:start viewer
    viewer = dv(id="toolbar", documents=[registration()])[
        dv.toolbar[
            dv.back(href="/", label="Case"),
            dv.title("Registration", "IV-Anmeldung 001.001"),  # a fixed title
            dv.pager(),
            dv.fit(),  # no zoom steps, only fit to width
            dv.spacer(),  # pushes the rest to the end
            c.pill("2 to check", appearance="warning", variant="outline"),
            c.button(  # the app's own control, as quiet as the viewer's
                icon="download",
                variant="ghost",
                size="sm",
                href="/sample-pages/anmeldung/1.svg",
                aria_label="Download",
            ),
        ],
        dv.pages(),  # no thumbnail rail
    ]
    # docs:end viewer
    # docs:start standard
    # dv.toolbar() without children is the standard composition:
    standard = dv.toolbar[dv.title(), dv.pager(), dv.zoom(), dv.fit()]  # noqa: F841
    # docs:end standard
    return example_page(
        title="Custom toolbar",
        intro=[
            y.p[
                "The toolbar is made of one control per part: ",
                y.code["back"],
                ", ",
                y.code["title"],
                ", ",
                y.code["pager"],
                ", ",
                y.code["zoom"],
                ", ",
                y.code["fit"],
                " and ",
                y.code["spacer"],
                ". ",
                y.code["dv.toolbar[...]"],
                " shows the controls it is given, in that order, mixed with any node of the app (a button, a pill, a menu).",
            ],
            y.p[
                "Without a title, ",
                y.code["dv.title()"],
                " follows the document in view; with one it stays fixed. ",
                "Parts can also be left out: this viewer has no thumbnail rail.",
            ],
        ],
        code=code(__file__, "viewer", "standard"),
        viewer=viewer,
        height="36rem",
    )
