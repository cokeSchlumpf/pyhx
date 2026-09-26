"""Drawer demo page + the fragments that supply its content."""

import htpy as y
import pyhx.components as c

from pyhx.core import WebAppRouter
from pyhx.utils import lorem_ipsum


router = WebAppRouter()


@router.fragment.get("/drawer/basic")
async def drawer_basic() -> y.Node:
    return c.drawer_content(y.p["Hello World"])


@router.fragment.get("/drawer/titled")
async def drawer_titled() -> y.Node:
    return c.drawer_content(
        y.p[
            "Drawers with a title get a heading row above the content. The close button (×) sits at the right of that row."
        ],
        title="Some Content",
    )


@router.fragment.get("/drawer/long")
async def drawer_long() -> y.Node:
    return c.drawer_content(
        y.fragment[
            y.p[
                "Scroll inside the drawer to see how its section overflows independently of the page below."
            ],
            lorem_ipsum(paragraphs=20),
        ],
        title="Long Content",
    )


@router.page("/drawer", title="Drawer")
async def drawer() -> y.Node:
    return c.container(
        y.article[
            y.h1["Drawer"],
            y.p[
                "A modal slide-over panel that enters from the right edge of the viewport. ",
                "Use it for focused detail views, edit forms, or any interaction that benefits from a dismissable overlay instead of a full page navigation.",
            ],
            y.h2["How it works"],
            y.p[
                "The drawer shell is rendered once by the page template and stays in the DOM for the life of the page. ",
                "A trigger element (typically a button) fetches a fragment that returns ",
                y.code["drawer_content(...)"],
                " marked with ",
                y.code['hx-swap-oob="innerHTML"'],
                "; htmx routes it to the persistent drawer's ",
                y.code["<section>"],
                " and replaces its children. A CSS ",
                y.code[":has(> aside > section > *)"],
                " rule then sees the section has children and slides the drawer in. ",
                "Closing posts to the close fragment, which OOB-swaps an empty section back in — the ",
                y.code[":has()"],
                " match drops, the drawer slides back out. The shell never moves, so the transitions run on the same DOM nodes every time.",
            ],
            y.h2["Wiring a trigger"],
            y.p[
                "Spread ",
                y.code["open_drawer_htmx_attributes(url)"],
                " into any element you want to act as a trigger. The fragment at that URL must return ",
                y.code["drawer_content(...)"],
                ".",
            ],
            y.pre[y.code["""\
import htpy as y
import pyhx.components as c


# Trigger anywhere on the page
c.button(
    "Open details",
    **c.open_drawer_htmx_attributes(item_details.url()),
)


# Fragment that produces the drawer body
@hx.fragment.get("/items/details")
async def item_details() -> y.Node:
    return c.drawer_content(
        y.p["Hello World"],
        title="Details",
    )
"""]],
            y.h2["Basic"],
            y.p["Minimal example — no title, single paragraph of content."],
            c.button(
                "Open basic drawer", **c.open_drawer_htmx_attributes(drawer_basic.url()),
            ),
            y.h2["With a title"],
            y.p[
                "Pass ",
                y.code["title"],
                " to render a heading row above the content. Omit it and the header collapses down to just the close button.",
            ],
            c.button(
                "Open titled drawer",
                **c.open_drawer_htmx_attributes(drawer_titled.url()),
            ),
            y.h2["Long content"],
            y.p[
                "The drawer's ",
                y.code["<section>"],
                " is the scroll container — the header (and its close button) stay pinned at the top regardless of how much content the body holds.",
            ],
            c.button(
                "Open scrolling drawer",
                **c.open_drawer_htmx_attributes(drawer_long.url()),
            ),
            y.h2["Closing"],
            y.p[
                "Two targets close the drawer: the × button in the header and the dimmed backdrop. ",
                "Both POST to the close fragment, which OOB-swaps an empty section back in — the persistent shell means the slide-out animation always runs on the same aside element.",
            ],
        ],
        width="medium",
    )
