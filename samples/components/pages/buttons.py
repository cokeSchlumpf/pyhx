"""Button demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from typing import get_args

from pyhx.core import WebAppRouter
from pyhx.components.variants import Appearance, Size, Variant
from samples.components._snippets import snippets

src = snippets(__file__)


APPEARANCES: tuple[Appearance, ...] = get_args(Appearance)
VARIANTS: tuple[Variant, ...] = get_args(Variant)
SIZES: tuple[Size, ...] = get_args(Size)


CELL = "padding: 0.5rem 1rem; text-align: left; vertical-align: middle;"


router = WebAppRouter()


@router.page("/button", title="Button")
async def buttons_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Button"],
            y.p[
                "A ",
                y.code["c.button"],
                " composes three independent axes: ",
                y.code["appearance"],
                " (color / semantic), ",
                y.code["variant"],
                " (emphasis: solid / outline / ghost), and ",
                y.code["size"],
                " (sm / md / lg). ",
                "Optional ",
                y.code["icon"],
                " + ",
                y.code["icon_position"],
                " add a leading or trailing icon, ",
                "or omit the label for an icon-only square button.",
            ],
            y.h2["Appearance × Variant"],
            y.p["At default size (", y.code["md"], ")."],
            c.example(
                # docs:start appearance_variant
                y.table(style="border-collapse: collapse; margin-block: 1rem;")[
                    y.thead[
                        y.tr[
                            y.th(style=CELL)[""],
                            [y.th(style=CELL)[v] for v in VARIANTS],
                        ]
                    ],
                    y.tbody[
                        [
                            y.tr[
                                y.th(style=CELL)[a],
                                [
                                    y.td(style=CELL)[c.button(a, appearance=a, variant=v)]
                                    for v in VARIANTS
                                ],
                            ]
                            for a in APPEARANCES
                        ]
                    ],
                ],
                # docs:end appearance_variant
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("appearance_variant"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Sizes"],
            y.p[
                "Each size shown with appearance ",
                y.code["primary"],
                ", variant ",
                y.code["solid"],
                ".",
            ],
            c.example(
                # docs:start sizes
                y.div(
                    style="display: flex; align-items: center; gap: 0.5rem; margin-block: 1rem;"
                )[[c.button(s, appearance="primary", size=s) for s in SIZES]],
                # docs:end sizes
                code=[("code", src.text("sizes"), "python")],
            ),
            y.h2["With icons"],
            c.example(
                # docs:start with_icons
                y.div(
                    style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-block: 1rem;"
                )[
                    c.button("Save", icon="save", appearance="primary"),
                    c.button("Next", icon="arrow-right", icon_position="right"),
                    c.button(
                        "Delete", icon="trash-2", appearance="danger", variant="outline"
                    ),
                ],
                # docs:end with_icons
                code=[("code", src.text("with_icons"), "python")],
            ),
            y.h2["Icon-only"],
            y.p[
                "Omit the label and pass ",
                y.code["icon"],
                " for a square icon-only button. Always pass ",
                y.code["aria_label"],
                " so the action is announced to screen readers.",
            ],
            c.example(
                # docs:start icon_only
                y.div(
                    style="display: flex; align-items: center; gap: 0.5rem; margin-block: 1rem;"
                )[
                    [
                        c.button(icon="settings", aria_label="Settings", size=s)
                        for s in SIZES
                    ],
                    c.button(icon="x", aria_label="Close", variant="ghost"),
                    c.button(
                        icon="trash-2",
                        aria_label="Delete",
                        appearance="danger",
                        variant="outline",
                    ),
                ],
                # docs:end icon_only
                code=[("code", src.text("icon_only"), "python")],
            ),
        ]
    )
