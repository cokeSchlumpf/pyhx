"""Split layout demo page.

A ``split_layout`` below a sticky page header: the main column scrolls, the
aside pins below the app-shell header *and* the page header, because the app
shell sets ``--hx-sticky-top`` to both heights. Narrow the window: below 58rem
of layout width (the sidebar's 260px don't count) the columns stack and the
aside scrolls with the page.
"""

import htpy as y
import pyhx.components as c

from pyhx.core import WebAppRouter
from pyhx.utils import lorem_ipsum


router = WebAppRouter()


@router.page("/split-layout", title="Split Layout")
async def split_layout() -> y.Node:
    return y.fragment[
        c.page_header(
            breadcrumbs=c.page_header.breadcrumbs(
                y.a(href="/")["Home"],
                "Split Layout",
            ),
            title=y.h1["Split Layout"],
            actions=c.button("Edit", appearance="primary"),
        ),
        c.container(
            c.split_layout(
                main=y.fragment[
                    y.article[
                        y.h2["Main column"],
                        y.p[
                            "Scroll the page: this column moves, the aside on the ",
                            "right stays pinned below the page header. Its offset ",
                            "comes from ",
                            y.code["--hx-sticky-top"],
                            ", which the app shell sets to the header plus the ",
                            "page header height.",
                        ],
                        y.p[
                            "The layout switches to one column when it is narrower ",
                            "than 58rem. It measures its own width (container ",
                            "query), so the sidebar is taken into account.",
                        ],
                    ],
                    [
                        y.article[y.h3[f"Section {i}"], lorem_ipsum(paragraphs=3)]
                        for i in range(1, 6)
                    ],
                ],
                aside=y.article[
                    y.h3["Aside"],
                    y.ul[[y.li[f"Event {i}"] for i in range(1, 9)]],
                    lorem_ipsum(max_words=12, paragraphs=2),
                ],
            ),
            width="wide",
        ),
    ]
