"""Example: several documents, grouped thumbnails, badges chosen by the app."""

import htpy as y

import pyhx.components as c
from pyhx.core import WebAppRouter
from samples.document_viewer import sample_document
from samples.document_viewer.sample_document import medical_report, registration

from ._layout import code, example_page

dv = c.document_viewer

router = WebAppRouter()


@router.page("/documents", title="Several documents")
async def documents() -> y.Node:
    # docs:start viewer
    viewer = dv(id="documents", documents=[registration(), medical_report()])[
        dv.toolbar(),  # title and counter follow the document in view
        dv.thumbnails(),  # grouped=None: headings because there are 2 documents
        dv.pages(),  # documents one after another, each starting with its title
    ]
    # docs:end viewer
    # docs:start ungrouped
    # Headings are up to the composition: force them for one document,
    # or leave them out for several.
    forced = dv.thumbnails(grouped=True)  # noqa: F841
    left_out = dv.thumbnails(grouped=False)  # noqa: F841
    # docs:end ungrouped

    return example_page(
        title="Several documents",
        intro=[
            y.p[
                "A viewer shows one or more documents. The page column shows them one after another, each starting with its title; previous and next run across documents. ",
                "The toolbar's title and counter follow the document in view: scroll down or click a page of the medical report.",
            ],
            y.p[
                "The thumbnail rail has a group per document. Its headings appear by default only with more than one document; ",
                y.code["grouped="],
                " decides otherwise.",
            ],
            y.p[
                "The badge on a thumbnail is the app's choice (",
                y.code["PageBadge"],
                ": text, meaning for screen readers, appearance); a page without one shows none. Here: the number of values read on a page, orange when some need checking.",
            ],
        ],
        code=y.fragment[
            code(__file__, "viewer", "ungrouped"),
            code(sample_document.__file__, "badges"),
        ],
        viewer=viewer,
    )
