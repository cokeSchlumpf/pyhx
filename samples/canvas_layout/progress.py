"""Progress bars in the canvas design.

Included by :mod:`samples.canvas_layout.main`. ``/progress-bars`` renders the
examples of the components sample (:mod:`samples.components.pages.progress_bar`)
in the canvas design: modes, motions, appearances, sizes, and a job panel.
"""

import htpy as y

import pyhx.components as c
from pyhx.components.view_model import Pct
from pyhx.core import WebAppRouter
from samples.components.pages.progress_bar import showcase

router = WebAppRouter()


def _job(title: str, pill: y.Node, bar: y.Node) -> y.Node:
    return c.card[
        c.card.header[c.card.title[y.h2[title]], pill],
        c.card.section[bar],
    ]


@router.page("/progress-bars", title="Progress bars")
async def progress_bars() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Progress bars"),
        c.card[
            c.card.header[
                c.card.title[y.h1["Progress bars"]],
                c.card.subtitle[
                    "c.progress_bar in the canvas design: static, working or waiting."
                ],
            ],
            c.card.section[showcase()],
        ],
        y.h2["In a job panel"],
        _job(
            "Document analysis",
            c.pill("Analysing 35 %", appearance="info"),
            c.progress_bar(
                Pct(0.35),
                working=True,
                label="Extracting findings",
                value_text="35 %",
                supporting_text="Page 4 of 12 · about 3 min left",
            ),
        ),
        _job(
            "Second intake",
            c.pill("Waiting, 2nd in line", appearance="neutral"),
            c.progress_bar(
                None,
                appearance="neutral",
                aria_label="Waiting, 2nd in line",
                supporting_text="Starts when the first analysis is done.",
            ),
        ),
        _job(
            "First intake",
            c.pill("Done", appearance="success"),
            c.progress_bar(
                Pct(1.0),
                appearance="success",
                aria_label="First intake, done",
                supporting_text="12 of 12 pages · finished at 09:41",
            ),
        ),
    ]
