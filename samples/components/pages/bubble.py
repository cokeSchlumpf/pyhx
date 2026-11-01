"""Bubble demo page."""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from typing import get_args

from pyhx.core import WebAppRouter
from pyhx.components.variants import Appearance
from samples.components._snippets import snippets

src = snippets(__file__)


APPEARANCES: tuple[Appearance, ...] = get_args(Appearance)


router = WebAppRouter()


@router.page("/bubble", title="Bubble")
async def bubble_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Bubble"],
            y.p[
                "A ",
                y.code["bubble"],
                " is a full-width, block-level container with rounded corners ",
                "and a semantically-tinted surface. It accepts any child ",
                "content and composes one axis: ",
                y.code["appearance"],
                ". For one-off colours, ",
                y.code["color"],
                " and ",
                y.code["text_color"],
                " override the appearance palette.",
            ],
            y.h2["All appearances"],
            c.example(
                # docs:start all_appearances
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    *[
                        c.bubble(appearance=appearance)[
                            y.strong[appearance.capitalize()],
                            " — a full-width bubble tinted with the ",
                            y.code[appearance],
                            " appearance.",
                        ]
                        for appearance in APPEARANCES
                    ]
                ],
                # docs:end all_appearances
                code=[
                    ("code", src.text("all_appearances"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Variants"],
            y.p[
                "Two emphasis levels via ",
                y.code["variant"],
                ": ",
                y.code["outline"],
                " (default, tinted surface) and ",
                y.code["solid"],
                " (filled with the appearance colour — the same palette as ",
                "solid buttons).",
            ],
            c.example(
                # docs:start variants
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    *[
                        c.bubble(appearance=appearance, variant="solid")[
                            y.strong[appearance.capitalize()],
                            " — a solid bubble filled with the ",
                            y.code[appearance],
                            " colour.",
                        ]
                        for appearance in APPEARANCES
                    ]
                ],
                # docs:end variants
                code=[("code", src.text("variants"), "python")],
            ),
            y.h2["Custom colours"],
            y.p[
                "Pass ",
                y.code["color"],
                " to override the background and ",
                y.code["text_color"],
                " to override the text. Either can be any CSS colour value, ",
                "including a design token such as ",
                y.code["var(--hx-color-info-050)"],
                ".",
            ],
            c.example(
                # docs:start custom_colors
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.bubble(color="#eef2ff", text_color="#3730a3")[
                        y.strong["Custom"],
                        " — a bubble with a bespoke background and text colour.",
                    ],
                    c.bubble(color="var(--hx-color-neutral-900)", text_color="#ffffff")[
                        y.strong["Inverted"],
                        " — a dark bubble built from theme tokens.",
                    ],
                ],
                # docs:end custom_colors
                code=[("code", src.text("custom_colors"), "python")],
            ),
            y.h2["Sizes"],
            y.p[
                "Two sizes: ",
                y.code["md"],
                " (standard) and ",
                y.code["sm"],
                " (smaller padding and font-size).",
            ],
            c.example(
                # docs:start sizes
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.bubble(size="md")[
                        y.strong["Medium"],
                        " — the standard bubble size.",
                    ],
                    c.bubble(size="sm")[
                        y.strong["Small"],
                        " — a more compact bubble.",
                    ],
                ],
                # docs:end sizes
                code=[("code", src.text("sizes"), "python")],
            ),
            y.h2["With nested components"],
            y.p[
                "Bubbles are plain containers — drop any components inside.",
            ],
            c.example(
                # docs:start nested
                c.bubble(appearance="success")[
                    y.h3(style="margin-top: 0;")["Upload complete"],
                    y.p["Your file was processed successfully."],
                    c.pill.container(
                        c.pill("Status", value="Done", appearance="success"),
                        c.pill("Rows", value="1,204", appearance="neutral"),
                    ),
                ],
                # docs:end nested
                code=[("code", src.text("nested"), "python")],
            ),
        ]
    )
