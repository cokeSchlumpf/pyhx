"""Icon demo page.

Shows PyHX's own SVG icons, the round badge (``circle=True``) and every
Feather icon name. ``IconName`` accepts both kinds.
"""

from typing import get_args

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from pyhx.core.primitives.icon_name import CustomIconName, FeatherIconName
from samples.components._snippets import snippets

src = snippets(__file__)


FEATHER_ICON_NAMES: tuple[FeatherIconName, ...] = get_args(FeatherIconName)
CUSTOM_ICON_NAMES: tuple[CustomIconName, ...] = get_args(CustomIconName)


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
                " renders an icon by name: one of the ",
                str(len(FEATHER_ICON_NAMES)),
                " Feather icons or one of PyHX's own SVG icons. ",
                y.code["IconName"],
                " is a ",
                y.code["Literal"],
                " union of both, so passing an unknown name fails at type-check ",
                "time. Every component with an ",
                y.code["icon"],
                " parameter (button, pill, message, navigation, …) accepts both.",
            ],
            y.h2["Example calls"],
            c.example(
                # docs:start example_calls
                c.icon("home"),
                c.icon("settings"),
                c.icon("swap"),
                c.icon("check-2"),
                # docs:end example_calls
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("example_calls"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2[f"Own icons ({len(CUSTOM_ICON_NAMES)})"],
            y.p[
                "One SVG file each in ",
                y.code["src/pyhx/static/icons"],
                ", inlined on the server — no JavaScript, and they survive htmx ",
                "swaps. To add one, drop the file there and add its name to ",
                y.code["CustomIconName"],
                "; a test keeps both in sync. A ",
                y.code["-2"],
                " suffix marks an icon whose Feather counterpart has the same name.",
            ],
            c.example(
                # docs:start custom
                y.div(
                    class_="hx-grid",
                    style="--hx-grid-columns: 4; margin-block: 1rem;",
                )[
                    [
                        y.div(style=CELL_STYLE)[
                            c.icon(name),
                            y.code(style=NAME_STYLE)[name],
                        ]
                        for name in CUSTOM_ICON_NAMES
                    ]
                ],
                # docs:end custom
                code=[("code", src.text("custom"), "python")],
            ),
            y.h2["In a circle"],
            y.p[
                y.code["circle=True"],
                " puts the icon in a round, tinted badge — e.g. in front of a ",
                "row in a ",
                y.code["card.list"],
                ". ",
                y.code["appearance"],
                " sets its colour, the same way as for pills.",
            ],
            c.example(
                # docs:start circle
                y.div(style="display: flex; gap: 0.75rem; margin-block: 1rem;")[
                    c.icon("check-2", circle=True, appearance="success"),
                    c.icon("swap", circle=True, appearance="danger"),
                    c.icon("exclamation", circle=True),
                    c.icon("document", circle=True, appearance="info"),
                    c.icon("pencil", circle=True, appearance="warning"),
                    c.icon("star", circle=True, appearance="primary"),
                ],
                # docs:end circle
                code=[("code", src.text("circle"), "python")],
            ),
            y.h2[f"All {len(FEATHER_ICON_NAMES)} Feather icons"],
            c.example(
                # docs:start gallery
                y.div(
                    class_="hx-grid",
                    style="--hx-grid-columns: 4; margin-block: 1rem;",
                )[
                    [
                        y.div(style=CELL_STYLE)[
                            c.icon(name),
                            y.code(style=NAME_STYLE)[name],
                        ]
                        for name in FEATHER_ICON_NAMES
                    ]
                ],
                # docs:end gallery
                code=[("code", src.text("gallery"), "python")],
            ),
        ]
    )
