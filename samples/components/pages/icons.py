"""Icon demo page — lists every feather icon name available via ``IconName``."""

from typing import cast, get_args

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from pyhx.core.primitives.icon_name import IconName
from samples.components._snippets import snippets

src = snippets(__file__)


ICON_NAMES: tuple[IconName, ...] = get_args(IconName)


router = WebAppRouter()


# Visible cell so each icon + name pair reads as a single unit.
CELL_STYLE = (
    "display: flex; "
    "flex-direction: column; "
    "align-items: center; "
    "gap: var(--hx-spacing-xs); "
    "padding: var(--hx-spacing-sm); "
    "background: var(--hx-color-neutral-100); "
    "border-radius: var(--hx-radius-sm); "
    "text-align: center;"
)

NAME_STYLE = "font-size: var(--hx-text-sm); color: var(--hx-color-neutral-600);"


@router.page("/icon", title="Icon")
async def icons_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Icon"],
            y.p[
                "An ",
                y.code["icon"],
                " renders a feather icon by name. ",
                y.code["IconName"],
                " is a ",
                y.code["Literal"],
                " union covering all ",
                str(len(ICON_NAMES)),
                " names, so passing an unknown one fails at type-check time.",
            ],
            y.h2["Example calls"],
            c.example(
                # docs:start example_calls
                c.icon("home"),
                c.icon("settings"),
                c.icon("alert-triangle"),
                # docs:end example_calls
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("example_calls"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2[f"All {len(ICON_NAMES)} icons"],
            c.example(
                # docs:start gallery
                y.div(
                    class_="hx-grid",
                    style="--hx-grid-columns: 4; margin-block: 1rem;",
                )[
                    [
                        y.div(style=CELL_STYLE)[
                            c.icon(cast(IconName, name)),
                            y.code(style=NAME_STYLE)[name],
                        ]
                        for name in ICON_NAMES
                    ]
                ],
                # docs:end gallery
                code=[("code", src.text("gallery"), "python")],
            ),
        ]
    )
