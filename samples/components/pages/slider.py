"""Slider demo page.

Renders the slider on its own scale, with per-thumb bounds, disabled and
inside a form (several instances submitting side by side). Dragging, clicking
the track and the keyboard are handled by ``pyhx.slider.js``.
"""

from functools import partial
from typing import Annotated

# docs:start imports
import htpy as y
import pyhx.components as c
from pyhx.components import Pct
# docs:end imports

from fastapi import Form
from pyhx.core import WebAppRouter
from pyhx.core.primitives import htmx
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


# docs:start form_handler
@router.fragment.post("/slider/submit")
async def submit(
    opacity: Annotated[float, Form()],
    period: Annotated[list[float], Form()],
) -> y.Node:
    return y.article(id="slider-result", **{"hx-swap-oob": "outerHTML"})[
        y.h3["Received"],
        y.ul[
            y.li[y.code["opacity"], f" = {opacity!r}"],
            y.li[y.code["period"], f" = {period!r}"],
        ],
    ]


# docs:end form_handler


# docs:start live_handler
@router.fragment.post("/slider/live")
async def live(
    brightness: Annotated[float, Form()],
    window: Annotated[list[float], Form()],
) -> y.Node:
    start, end = window
    return y.ul[
        y.li["Brightness: ", y.strong[f"{brightness:g}%"]],
        y.li["Window: ", y.strong[f"{start:g}:00 – {end:g}:00"], f" ({end - start:g} h)"],
    ]


# docs:end live_handler


@router.page("/slider", title="Slider")
async def slider_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Slider"],
            y.p[
                "Pick one or more values on a scale — a single value, a range ",
                "(two thumbs) or gradient stops (three or more thumbs). Every ",
                "thumb submits its value through a hidden input, so the slider ",
                "works in any form. Drag a thumb or click the track; with a ",
                "focused thumb, the arrow keys move it by one step, ",
                y.kbd["Page Up"],
                " / ",
                y.kbd["Page Down"],
                " by ten and ",
                y.kbd["Home"],
                " / ",
                y.kbd["End"],
                " to its bounds.",
            ],
            y.h2["Single value"],
            y.p[
                "The default scale runs from 0 to 100 in steps of 1. The range ",
                "fills the track up to the thumb.",
            ],
            c.example(
                # docs:start single
                c.slider("volume", value=40),
                # docs:end single
                code=[
                    ("code", src.text("single"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Own scale and step"],
            y.p[
                y.code["min"],
                ", ",
                y.code["max"],
                " and ",
                y.code["step"],
                " define the scale. Values are snapped to the step (counted ",
                "from ",
                y.code["min"],
                ") — fractional steps work too.",
            ],
            c.example(
                # docs:start scale
                c.slider("ratio", value=0.3, min=0, max=1, step=0.1),
                # docs:end scale
                code=[("code", src.text("scale"), "python")],
            ),
            y.h2["Two thumbs"],
            y.p[
                "A sequence of values renders one thumb each; with two thumbs ",
                "the range fills the track between them. Thumbs never cross: ",
                "values must be ascending, and each neighbour acts as a bound.",
            ],
            c.example(
                # docs:start double
                c.slider(
                    "years",
                    value=[
                        c.SliderThumb(2022, label="From"),
                        c.SliderThumb(2026, label="To"),
                    ],
                    min=2020,
                    max=2030,
                ),
                # docs:end double
                code=[("code", src.text("double"), "python")],
            ),
            y.h2["Bounds per thumb"],
            y.p[
                y.code["SliderThumb"],
                " narrows the range a single thumb may move in — e.g. the ",
                "stops of a gradient, where the first stop stays in the lower ",
                "third and the last in the upper third. With three or more ",
                "thumbs there is no range.",
            ],
            c.example(
                # docs:start bounds
                c.slider(
                    "stops",
                    value=[
                        c.SliderThumb(0, max=30, label="Start"),
                        c.SliderThumb(50, min=20, max=80, label="Middle"),
                        c.SliderThumb(100, min=70, label="End"),
                    ],
                ),
                # docs:end bounds
                code=[("code", src.text("bounds"), "python")],
            ),
            y.h2["Disabled"],
            y.p[
                "Thumbs become inert; the hidden inputs keep submitting so the ",
                "value isn't lost on save.",
            ],
            c.example(
                # docs:start disabled
                c.slider("locked", value=(20, 60), disabled=True),
                # docs:end disabled
                code=[("code", src.text("disabled"), "python")],
            ),
            y.h2["In a form"],
            y.p[
                "Several sliders side by side in one form, plugged into ",
                y.code["c.form_field"],
                " via ",
                y.code["functools.partial"],
                ". All hidden inputs of a slider share its ",
                y.code["name"],
                ": one thumb submits a single value, two or more a list.",
            ],
            c.example(
                # docs:start form
                y.form(
                    **htmx(hx_post=submit.url(), hx_swap="none", as_dict=True)
                )[
                    c.form_field(
                        "opacity",
                        "Opacity",
                        partial(c.slider, min=0, max=1, step=0.05),
                        wrapper="div",
                        value=0.75,
                    ),
                    c.form_field(
                        "period",
                        "Period",
                        partial(c.slider, min=2020, max=2030),
                        wrapper="div",
                        value=(2022, 2026),
                        help_text="Start and end year.",
                    ),
                    c.button("Submit", appearance="primary", type="submit"),
                ],
                # docs:end form
                code=[
                    ("code", src.text("form"), "python"),
                    ("handler", src.text("form_handler"), "python"),
                ],
            ),
            y.article(id="slider-result")[
                y.h3["Received"],
                y.p["Click Submit to see the submitted values here."],
            ],
            y.h2["Live value on change"],
            y.p[
                "The slider dispatches a bubbling ",
                y.code["change"],
                " event from its hidden input when a value settles (pointer ",
                "released, key pressed). A form with ",
                y.code['hx-trigger="change"'],
                " picks it up like any other control and posts all values; ",
                "the response replaces the output below.",
            ],
            c.example(
                # docs:start live
                y.form(
                    **htmx(
                        hx_post=live.url(),
                        hx_trigger="change",
                        hx_target="#slider-live-output",
                        as_dict=True,
                    )
                )[
                    c.form_field(
                        "brightness",
                        "Brightness",
                        partial(c.slider, step=5),
                        wrapper="div",
                        value=60,
                    ),
                    c.form_field(
                        "window",
                        "Time window",
                        partial(c.slider, min=0, max=24),
                        wrapper="div",
                        value=(8, 17),
                    ),
                    y.output(id="slider-live-output")[
                        y.ul[
                            y.li["Brightness: ", y.strong["60%"]],
                            y.li["Window: ", y.strong["8:00 – 17:00"], " (9 h)"],
                        ]
                    ],
                ],
                # docs:end live
                code=[
                    ("code", src.text("live"), "python"),
                    ("handler", src.text("live_handler"), "python"),
                ],
            ),
            y.h2["Elements"],
            y.p[
                "The visual elements are also available as sub-builders — ",
                y.code["slider.container"],
                ", ",
                y.code["slider.track"],
                ", ",
                y.code["slider.range"],
                " and ",
                y.code["slider.thumb"],
                " — positioned as a ",
                y.code["Pct"],
                " along the track. This one has thumbs at both edges: the ",
                "container reserves half a thumb on every side, so they stay ",
                "inside.",
            ],
            c.example(
                # docs:start elements
                c.slider.container[
                    c.slider.track[
                        c.slider.range(),
                        c.slider.thumb(Pct.of(0), aria_label="Start"),
                        c.slider.thumb(Pct.of(100), aria_label="End"),
                    ]
                ],
                # docs:end elements
                code=[("code", src.text("elements"), "python")],
            ),
        ]
    )
