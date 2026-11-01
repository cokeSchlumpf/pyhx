"""Segment control demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from typing import get_args

from pyhx.core import WebAppRouter
from pyhx.components.variants import Size
from samples.components._snippets import snippets

src = snippets(__file__)


SIZES: tuple[Size, ...] = get_args(Size)


VIEW_OPTIONS = [
    c.Option(label="List", value="list"),
    c.Option(label="Grid", value="grid"),
    c.Option(label="Kanban", value="kanban"),
]


RANGE_OPTIONS = [
    c.Option(label="Day", value="day"),
    c.Option(label="Week", value="week"),
    c.Option(label="Month", value="month"),
    c.Option(label="Year", value="year"),
]


router = WebAppRouter()


@router.page("/segment-control", title="Segment control")
async def segment_control_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Segment control"],
            y.p[
                "A ",
                y.code["c.segment_control"],
                " renders a row of buttons that act as a single-select group. ",
                "Under the hood it is a real ",
                y.code['<input type="radio">'],
                " group wrapped in labels — keyboard navigation, focus, and form ",
                "submission all work without JavaScript. The selected state is driven ",
                "by CSS ",
                y.code[":has(:checked)"],
                ".",
            ],
            y.h2["Default"],
            c.example(
                # docs:start default
                y.div(style="margin-block: 1rem;")[
                    c.segment_control("view", VIEW_OPTIONS, value="list"),
                ],
                # docs:end default
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("default"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Sizes"],
            c.example(
                # docs:start sizes
                y.div(
                    style="display: flex; align-items: center; gap: 1rem; margin-block: 1rem;"
                )[
                    [
                        c.segment_control(
                            f"range-{s}", RANGE_OPTIONS, value="week", size=s
                        )
                        for s in SIZES
                    ]
                ],
                # docs:end sizes
                code=[("code", src.text("sizes"), "python")],
            ),
            y.h2["No selection"],
            y.p[
                "Omit ",
                y.code["value"],
                " to render the control with no option pre-selected.",
            ],
            c.example(
                # docs:start no_selection
                y.div(style="margin-block: 1rem;")[
                    c.segment_control("view-empty", VIEW_OPTIONS),
                ],
                # docs:end no_selection
                code=[("code", src.text("no_selection"), "python")],
            ),
            y.h2["Inside a form"],
            y.p[
                "Submit the form below to confirm the selected value is posted under ",
                y.code["name"],
                ". The page reloads with the chosen value echoed in the URL.",
            ],
            c.example(
                # docs:start in_form
                y.form(method="get", style="margin-block: 1rem;")[
                    y.div(
                        style="display: flex; align-items: center; gap: 1rem;"
                    )[
                        c.segment_control("range", RANGE_OPTIONS, value="month"),
                        c.button("Submit", appearance="primary", type="submit"),
                    ]
                ],
                # docs:end in_form
                code=[("code", src.text("in_form"), "python")],
            ),
        ]
    )
