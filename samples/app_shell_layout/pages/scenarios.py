"""Layout-scenario demo pages.

Each page exercises a specific App Shell layout situation: short vs long
sidebar, both columns long, and the ``mode="app"`` variant with the
footer pinned to the viewport bottom.
"""

import htpy as y
import pyhx.components as c

from pyhx.core import PageResponse, WebAppRouter
from pyhx.page_templates import AppShell
from pyhx.utils import lorem_ipsum


router = WebAppRouter()


@router.page("/long-main-content", title="Long Main Content")
async def long_main_content() -> PageResponse:
    return PageResponse(
        node=c.container(
            y.article[
                y.h1["Long Main Content"],
                y.p[
                    "Main (20 paragraphs) is longer than the sidebar (3 paragraphs). ",
                    "Expected: header pinned at top; the sidebar's short content sticks just below the header ",
                    "(its inner sticky engages because the sidebar's parent stretches to the tall grid row); ",
                    "main scrolls past it; footer appears below main content at the end.",
                ],
                y.hr,
                lorem_ipsum(paragraphs=20),
            ],
            width="medium",
        ),
        page_template=AppShell(
            sidebar_content=y.div[lorem_ipsum(max_words=12, paragraphs=3)]
        ),
    )


@router.page("/long-nav-content", title="Long Navigation Content")
async def long_nav_content() -> PageResponse:
    return PageResponse(
        node=c.container(
            y.article[
                y.h1["Long Navigation Content"],
                y.p[
                    "Sidebar (22 paragraphs) is longer than main (one paragraph). ",
                    "Mirror of the long-main case: header pinned at top; main's short content sticks just below the header ",
                    "while the long sidebar keeps scrolling; footer appears below the sidebar at the end.",
                ],
            ],
            width="medium",
        ),
        page_template=AppShell(
            sidebar_content=y.div[lorem_ipsum(max_words=12, paragraphs=22)]
        ),
    )


@router.page("/long-content", title="Long Content")
async def long_content() -> PageResponse:
    return PageResponse(
        node=c.container(
            y.article[
                y.h1["Long Content"],
                y.p[
                    "Both columns are longer than the viewport (sidebar 15 ¶, main 25 ¶). ",
                    "Neither inner sticky engages — each column fills its grid cell entirely, ",
                    "so there's no slack for sticky to move within. ",
                    "Both columns scroll together with the page; footer appears below all content at the end.",
                ],
                y.hr,
                lorem_ipsum(paragraphs=25),
            ],
            width="medium",
        ),
        page_template=AppShell(
            sidebar_content=y.div[lorem_ipsum(max_words=12, paragraphs=15)]
        ),
    )


@router.page("/app-mode", title="App Mode")
async def app_mode() -> PageResponse:
    return PageResponse(
        node=c.container(
            y.article[
                y.h1["App Mode"],
                y.p[
                    "Same content as Long Content, but rendered with mode='app'. ",
                    "Expected: identical scroll behavior to page mode, except the footer is pinned to the viewport bottom ",
                    "(via position: sticky; bottom: 0) so it stays visible at every scroll position instead of sitting below content at the end.",
                ],
                y.hr,
                lorem_ipsum(paragraphs=25),
            ],
            width="medium",
        ),
        page_template=AppShell(
            sidebar_content=y.div[lorem_ipsum(max_words=12, paragraphs=15)], mode="app"
        ),
    )
