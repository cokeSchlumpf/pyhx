"""Pill demo page."""

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


@router.page("/pill", title="Pill")
async def pills_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Pill"],
            y.p[
                "A ",
                y.code["pill"],
                " renders a short, semantically-coloured label, optionally ",
                "followed by a secondary ",
                y.code["value"],
                " segment. It composes one axis: ",
                y.code["appearance"],
                ".",
            ],
            y.h2["All appearances"],
            c.example(
                # docs:start all_appearances
                c.pill.container(
                    *[c.pill(appearance, appearance=appearance) for appearance in APPEARANCES],
                    style="margin-block: 1rem;",
                ),
                # docs:end all_appearances
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("all_appearances"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["With value"],
            y.p[
                "Passing ",
                y.code["value"],
                " renders a second segment next to the label — useful for ",
                "label/value pairs like status, counts, or version tags.",
            ],
            c.example(
                # docs:start with_value
                c.pill.container(
                    c.pill("Version", value="1.2.0", appearance="neutral"),
                    c.pill("Plan", value="Pro", appearance="primary"),
                    c.pill("Type", value="Draft", appearance="info"),
                    c.pill("Status", value="Active", appearance="success"),
                    c.pill("Priority", value="High", appearance="warning"),
                    c.pill("Errors", value="42", appearance="danger"),
                    style="margin-block: 1rem;",
                ),
                # docs:end with_value
                code=[("code", src.text("with_value"), "python")],
            ),
            y.h2["With close button"],
            y.p[
                "Pass ",
                y.code["c.pill.button(aria_label=...)"],
                " into the ",
                y.code["button"],
                " slot to turn a pill into a removable chip. ",
                y.code["c.pill.button"],
                " is the chip-scoped button — it inherits the chip's ",
                "metrics directly instead of fighting the cascade against ",
                y.code[".hx-button"],
                ". Defaults to the ",
                y.code["x"],
                " icon; pass any ",
                y.code["IconName"],
                " to override.",
            ],
            y.h3["Plain"],
            c.example(
                # docs:start close_plain
                c.pill.container(
                    c.pill(
                        "Feature",
                        appearance="info",
                        button=c.pill.button(aria_label="Remove Feature"),
                    ),
                    c.pill(
                        "Bug",
                        appearance="danger",
                        button=c.pill.button(aria_label="Remove Bug"),
                    ),
                    c.pill(
                        "Docs",
                        appearance="neutral",
                        button=c.pill.button(aria_label="Remove Docs"),
                    ),
                    style="margin-block: 1rem;",
                ),
                # docs:end close_plain
                code=[("code", src.text("close_plain"), "python")],
            ),
            y.h3["With value"],
            c.example(
                # docs:start close_value
                c.pill.container(
                    c.pill(
                        "Status",
                        value="Active",
                        appearance="success",
                        button=c.pill.button(aria_label="Remove Status filter"),
                    ),
                    c.pill(
                        "Priority",
                        value="High",
                        appearance="warning",
                        button=c.pill.button(aria_label="Remove Priority filter"),
                    ),
                    c.pill(
                        "Errors",
                        value="42",
                        appearance="danger",
                        button=c.pill.button(aria_label="Remove Errors filter"),
                    ),
                    style="margin-block: 1rem;",
                ),
                # docs:end close_value
                code=[("code", src.text("close_value"), "python")],
            ),
        ]
    )
