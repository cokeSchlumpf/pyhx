"""Loading indicators in the canvas design.

Included by :mod:`samples.canvas_layout.main`. ``/loading-indicators``
renders the examples of the components sample
(:mod:`samples.components.pages.loading_indicator`) in the canvas design:
kinds, sizes, appearances and the places the mark is used in.
"""

import htpy as y

import pyhx.components as c
from pyhx.core import WebAppRouter
from samples.components.pages.loading_indicator import showcase

router = WebAppRouter()


@router.page("/loading-indicators", title="Loading indicators")
async def loading_indicators() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Loading indicators"),
        c.card[
            c.card.header[
                c.card.title[y.h1["Loading indicators"]],
                c.card.subtitle[
                    "c.loading_indicator in the canvas design: this is happening right now."
                ],
            ],
            c.card.section[showcase()],
        ],
    ]
