"""Metric tile demo page."""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from typing import get_args

from pyhx.components.primitives.metric_tile import MetricTileAppearance
from pyhx.components.variants import Appearance
from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


# The tile widens the shared Appearance axis by one extra colour: "purple".
APPEARANCES: tuple[MetricTileAppearance, ...] = (*get_args(Appearance), "purple")


router = WebAppRouter()


@router.page("/metric-tile", title="Metric Tile")
async def metric_tile_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Metric Tile"],
            y.p[
                "A ",
                y.code["metric_tile"],
                " presents a single number with a short label and optional ",
                "supporting text — the building block of dashboard-style ",
                "summaries such as coverage, open questions, or completion ",
                "counts.",
            ],
            y.p[
                "The component renders what it is given: ",
                y.code["value"],
                ", ",
                y.code["label"],
                " and ",
                y.code["supporting_text"],
                " are plain nodes, and formatting the metric stays with the ",
                "calling application. It composes one axis: ",
                y.code["appearance"],
                " — the shared appearance vocabulary plus one extra colour, ",
                y.code["purple"],
                ".",
            ],
            y.h2["All appearances"],
            y.p[
                "The appearance drives the accent used for the border, the ",
                "tinted surface and the value colour.",
            ],
            c.example(
                # docs:start all_appearances
                y.div(class_="hx-grid", style="--hx-grid-columns: 4;")[
                    *[
                        c.metric_tile(
                            value="92%",
                            label=f"{appearance.capitalize()} appearance",
                            appearance=appearance,
                        )
                        for appearance in APPEARANCES
                    ]
                ],
                # docs:end all_appearances
                code=[
                    ("code", src.text("all_appearances"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["With supporting text"],
            y.p[
                "Passing ",
                y.code["supporting_text"],
                " adds a third line below the label — use it for the scope or ",
                "the reference period the metric applies to. Omitting it (the ",
                "default) renders no extra element at all.",
            ],
            c.example(
                # docs:start supporting_text
                y.div(class_="hx-grid", style="--hx-grid-columns: 2;")[
                    c.metric_tile(
                        value="7",
                        label="Open questions",
                        supporting_text="Across all stages",
                        appearance="warning",
                    ),
                    c.metric_tile(
                        value="7",
                        label="Open questions",
                        appearance="warning",
                    ),
                ],
                # docs:end supporting_text
                code=[("code", src.text("supporting_text"), "python")],
            ),
            y.h2["Dashboard row"],
            y.p[
                "Tiles stretch to the height of their row, so a set of them ",
                "stays aligned even when only some carry supporting text. Lay ",
                "them out with the ",
                y.code["hx-grid"],
                " utility and a span per tile.",
            ],
            c.example(
                # docs:start dashboard
                y.div(class_="hx-grid")[
                    c.metric_tile(
                        value="92%",
                        label="Evidence coverage",
                        supporting_text="Up 4 points since last review",
                        appearance="info",
                        class_="hx-grid-span-3",
                    ),
                    c.metric_tile(
                        value="184",
                        label="Documents processed",
                        appearance="neutral",
                        class_="hx-grid-span-3",
                    ),
                    c.metric_tile(
                        value="7",
                        label="Open questions",
                        supporting_text="Across all stages",
                        appearance="warning",
                        class_="hx-grid-span-3",
                    ),
                    c.metric_tile(
                        value="3",
                        label="Blocking findings",
                        appearance="danger",
                        class_="hx-grid-span-3",
                    ),
                ],
                # docs:end dashboard
                code=[("code", src.text("dashboard"), "python")],
            ),
            y.h2["Composed value and label"],
            y.p[
                "Because every slot takes a node, the value can carry a unit, ",
                "a delta, or any other markup, and the label can hold inline ",
                "elements.",
            ],
            c.example(
                # docs:start composed
                y.div(class_="hx-grid", style="--hx-grid-columns: 3;")[
                    c.metric_tile(
                        value=y.fragment[
                            "1.24",
                            y.small(style="font-size: 0.5em; margin-left: 0.25em;")[
                                "M t CO₂e"
                            ],
                        ],
                        label="Total emissions",
                        appearance="purple",
                    ),
                    c.metric_tile(
                        value=y.fragment[
                            "+12",
                            y.span(style="margin-left: 0.25em;")[
                                c.icon("trending-up"),
                            ],
                        ],
                        label="Suppliers onboarded",
                        supporting_text="Compared to Q3",
                        appearance="success",
                    ),
                    c.metric_tile(
                        value="64%",
                        label=y.fragment["Coverage of ", y.strong["Tier 1"]],
                        appearance="primary",
                    ),
                ],
                # docs:end composed
                code=[("code", src.text("composed"), "python")],
            ),
            y.h2["Semantics and extra attributes"],
            y.p[
                "The tile renders a description list — ",
                y.code["<dl>"],
                " with the label as ",
                y.code["<dt>"],
                " and the value (plus supporting text) as ",
                y.code["<dd>"],
                " — so the pairing survives without styling. CSS ",
                y.code["order"],
                " puts the value above the label visually. Any extra keyword ",
                "argument is forwarded to the outer ",
                y.code["<dl>"],
                ", which is how a tile gets an ",
                y.code["id"],
                ", an ",
                y.code["aria-label"],
                " that reads value and label as one phrase, or htmx attributes ",
                "for live updates.",
            ],
            c.example(
                # docs:start attributes
                c.metric_tile(
                    value="92%",
                    label="Evidence coverage",
                    appearance="info",
                    id="evidence-coverage",
                    aria_label="Evidence coverage: 92 percent",
                ),
                # docs:end attributes
                code=[("code", src.text("attributes"), "python")],
            ),
        ]
    )
