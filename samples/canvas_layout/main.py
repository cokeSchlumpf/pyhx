"""Canvas Shell layout sample.

Run with::

    poetry run fastapi dev samples/canvas_layout/main.py

One page per ``CanvasShell`` mode (``centered``, ``wide``, ``full``), each with
breadcrumbs and placeholder content, plus a dossier page with a
``split_layout`` (main column and sticky aside below the breadcrumbs). The placeholders are plain Pico
``<article>`` elements; the canvas card component comes in a later step.
"""

import htpy as y
import pyhx.components as c

from pyhx.core import PageResponse, RequestContext, WebApp
from pyhx.page_templates import CanvasShell
from pyhx.utils import lorem_ipsum


def header_content() -> y.Node:
    """Evaluated per request: shows the current user next to a static label.

    The shell draws the separator line between the direct children.
    """
    return [
        y.span["Muster AG"],
        y.span[RequestContext.get().user.display_name],
    ]


hx = WebApp(
    title="Canvas Layout",
    default_page_template=CanvasShell(header_content=header_content),
)


def _modes() -> y.Node:
    return y.ul[
        y.li[y.a(href="/")["centered"], " — at most 72rem, the default"],
        y.li[y.a(href="/wide")["wide"], " — at most --hx-container-width-wide"],
        y.li[y.a(href="/full")["full"], " — full width, no padding"],
        y.li[y.a(href="/dossier")["dossier"], " — split layout with a sticky aside"],
    ]


@hx.page("/", title="Centered")
async def centered() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Centered"),
        y.article[
            y.h1["Centered"],
            y.p["The content column is centered and at most 72rem wide."],
            _modes(),
        ],
        y.article[lorem_ipsum(paragraphs=12)],
    ]


@hx.page("/wide", title="Wide")
async def wide() -> PageResponse:
    return PageResponse(
        node=y.div[
            c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Wide"),
            y.article[
                y.h1["Wide"],
                y.p["Same design, wider content column — e.g. for wide tables."],
                _modes(),
            ],
            y.article[lorem_ipsum(paragraphs=4)],
        ],
        page_template=CanvasShell(header_content=header_content, mode="wide"),
    )


@hx.page("/full", title="Full")
async def full() -> PageResponse:
    pane = "margin: 0; border-radius: 0; min-height: calc(100dvh - 3.5rem);"
    return PageResponse(
        node=y.div(
            style="display: grid; grid-template-columns: 12rem 1fr 24rem; gap: 1px;"
        )[
            y.article(style=pane)["Thumbnails"],
            y.article(style=pane)[
                y.h1["Full"],
                y.p["Full viewport width without padding, e.g. a document viewer."],
                _modes(),
            ],
            y.article(style=pane)["Extracted values"],
        ],
        page_template=CanvasShell(header_content=header_content, mode="full"),
    )


@hx.page("/dossier", title="Dossier")
async def dossier() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Meine Dossiers"], "IV-2026-0142"),
        c.split_layout(
            main=y.fragment[
                y.article[
                    y.h1["Dossier IV-2026-0142"],
                    y.p[
                        "The breadcrumbs span both columns. Scroll: the aside ",
                        "pins below the top bar (",
                        y.code["--hx-sticky-top"],
                        ") once it reaches it.",
                    ],
                    _modes(),
                ],
                [
                    y.article[y.h2[f"Document {i}"], lorem_ipsum(paragraphs=3)]
                    for i in range(1, 6)
                ],
            ],
            aside=y.article[
                y.h2["Verlauf"],
                y.ul[[y.li[f"Event {i}"] for i in range(1, 9)]],
            ],
        ),
    ]


app = hx.create_app()
