"""Timeline demo page — blank scaffold for the ``timeline`` skeleton component.

Reserves the route and the sample-app wiring for the timeline. The component
is a skeleton for now, so this page just renders the placeholder; add live
demos here as the component grows.
"""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.page("/timeline", title="Timeline")
async def timeline_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Timeline"],
            y.p[
                "Zoomable timeline with icon markers and drill-down details. ",
                "The component is a skeleton for now and renders a placeholder.",
            ],
            y.h2["Default"],
            c.example(
                # docs:start default
                c.timeline(),
                # docs:end default
                code=[
                    ("code", src.text("default"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
        ]
    )
