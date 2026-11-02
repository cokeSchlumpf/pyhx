"""Document viewer sample (T-010): the draft API in common scenarios.

Run with::

    poetry run fastapi dev samples/document_viewer/main.py

Each example page explains a scenario, shows its code (cut from the page's own
module, so the code shown is the code that runs) and the live viewer below:
the basic viewer, several documents, marks, notes, a custom toolbar and a
case page with everything together, using ``c.document_viewer`` and
its view model; the page images are SVGs
served by this sample (:mod:`samples.document_viewer.sample_document`).
"""

from pathlib import Path

import htpy as y

import pyhx.components as c
from pyhx.core import WebApp
from pyhx.page_templates import CanvasShell

from .pages import basic, case, documents, marks, notes, toolbar
from .pages._layout import links
from .sample_document import register_routes

HERE = Path(__file__).parent


hx = WebApp(
    title="Document Viewer",
    default_page_template=CanvasShell(
        header_content=lambda: [y.span["T-010 draft"]], mode="wide"
    ),
    static_dirs=[HERE / "static"],
    configure_fastapi_app=[register_routes],
)

for module in (basic, documents, marks, notes, toolbar, case):
    hx.include_router(module.router)

_GLANCE = """dv = c.document_viewer

dv(id="doc", documents=[Document(...), ...])[
    dv.toolbar(),                 # or dv.toolbar[dv.back(...), dv.title(), dv.pager(),
                                  #               dv.zoom(), dv.fit(), dv.spacer(), <own>]
    dv.thumbnails(grouped=None),  # a group per document, PageBadge per page
    dv.pages(),                   # Mark (box, MarkStyle) and Note (pin) per page
    dv.sidebar[...],              # the app's content, linked by annotation ids
]

# link app content:  data-hx-document-annotation="doc:<annotation id>"  (+ aria-pressed)
# listen:            hx-document:annotation-select  {viewer, id, kind}
# script:            pyhx.documentViewer("doc").activate(id) / clear() / goTo("<doc>:<page>")"""


@hx.page("/", title="Document viewer")
async def index() -> y.Node:

    return y.div(style="display: flex; flex-direction: column; gap: 1rem;")[
        y.h1(style="margin: 0;")["Document viewer"],
        y.p[
            "Draft of ",
            y.code["c.document_viewer"],
            " (T-010) for reviewing the API: each example explains a scenario, shows its code and the live viewer.",
        ],
        links(),
        y.h2["The API at a glance"],
        c.code([("API", _GLANCE, "python")], max_height=None),
    ]


app = hx.create_app()
