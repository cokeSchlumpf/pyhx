"""Progress bar demo page.

``showcase()`` renders every mode, motion, appearance and size with its code;
the components sample (plain design) shows it at ``/progress-bar``, the
canvas layout sample at ``/progress-bars``.
"""

import htpy as y

# docs:start imports
import pyhx.components as c
from pyhx.components.view_model import Pct

# docs:end imports
from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()


def _grid(*items: y.Node) -> y.Node:
    # Up to three columns, one at phone width.
    return y.div(
        style="display: grid; gap: 1.25rem 2rem;"
        " grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));"
    )[items]


def showcase() -> y.Node:
    """The examples of the progress bar, each with its code."""
    return [
        y.h2["Modes"],
        y.p[
            "A bar with a value is ",
            y.strong["static"],
            " (a value that stands still) or ",
            y.strong["working"],
            " (",
            y.code["working=True"],
            ": its filled part moves while the value stays readable). Without a value (",
            y.code["None"],
            ") it is ",
            y.strong["waiting"],
            ": a segment travels along the track, e.g. for a job in the queue.",
        ],
        c.example(
            # docs:start modes
            _grid(
                c.progress_bar(
                    Pct(0.35),
                    label="Pages rendered",
                    value_text="35 %",
                    supporting_text="A value that stands still.",
                ),
                c.progress_bar(
                    Pct(0.35),
                    working=True,
                    label="Analysing",
                    value_text="35 %",
                    supporting_text="Extracting findings · page 4 of 12",
                ),
                c.progress_bar(
                    None,
                    label="Waiting, 2nd in line",
                    supporting_text="Starts when the first job is done.",
                ),
            ),
            # docs:end modes
            code=[
                ("code", src.text("modes"), "python"),
                ("imports", src.text("imports"), "python"),
            ],
        ),
        y.h2["Motion of a working bar"],
        y.p[
            y.code["motion"],
            " chooses the movement: ",
            y.code["sheen"],
            " (the default, calm), ",
            y.code["stripes"],
            " (visible from afar) or ",
            y.code["pulse"],
            " (quiet, e.g. for many bars in a list). With reduced motion set in the system, nothing moves.",
        ],
        c.example(
            # docs:start motion
            _grid(
                *[
                    c.progress_bar(
                        Pct(0.6),
                        working=True,
                        motion=motion,
                        label=motion.capitalize(),
                        value_text="60 %",
                    )
                    for motion in ("sheen", "stripes", "pulse")
                ]
            ),
            # docs:end motion
            code=[("code", src.text("motion"), "python")],
        ),
        y.h2["Appearances"],
        y.p[
            y.code["appearance"],
            " colours the filled part; ",
            y.code["primary"],
            " is the default (in the canvas design the text colour). Name the state in a text too: colour alone doesn't carry it.",
        ],
        c.example(
            # docs:start appearances
            _grid(
                c.progress_bar(Pct(0.48), label="primary", value_text="48 %"),
                c.progress_bar(
                    Pct(0.48), appearance="info", label="info", value_text="48 %"
                ),
                c.progress_bar(
                    Pct(0.48), appearance="neutral", label="neutral", value_text="48 %"
                ),
                c.progress_bar(
                    Pct(1.0), appearance="success", label="Done", value_text="100 %"
                ),
                c.progress_bar(
                    Pct(0.83),
                    appearance="warning",
                    label="Partly done",
                    value_text="83 %",
                ),
                c.progress_bar(
                    Pct(0.6),
                    appearance="danger",
                    label="Failed",
                    value_text="Stopped at 60 %",
                ),
            ),
            # docs:end appearances
            code=[("code", src.text("appearances"), "python")],
        ),
        y.h2["Sizes and texts"],
        y.p[
            y.code["size"],
            " sets the bar's height: ",
            y.code["sm"],
            " (e.g. in a table cell), ",
            y.code["md"],
            " (the default) or ",
            y.code["lg"],
            ". Without ",
            y.code["label"],
            ", ",
            y.code["value_text"],
            " and ",
            y.code["supporting_text"],
            " the bar stands alone; give it an ",
            y.code["aria_label"],
            " then.",
        ],
        c.example(
            # docs:start sizes
            _grid(
                c.progress_bar(Pct(0.7), size="sm", aria_label="Pages rendered"),
                c.progress_bar(
                    Pct(0.7),
                    working=True,
                    label="Upload",
                    value_text="7 of 10 files",
                ),
                c.progress_bar(
                    Pct(0.7),
                    working=True,
                    size="lg",
                    label="Analysing",
                    value_text="70 %",
                    supporting_text="Finding contradictions · about 1 min left",
                ),
            ),
            # docs:end sizes
            code=[("code", src.text("sizes"), "python")],
        ),
    ]


@router.page("/progress-bar", title="Progress Bar")
async def progress_bar_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Progress Bar"],
            y.p[
                "A ",
                y.code["progress_bar"],
                " shows how far a piece of work has got, as a filled bar on a track, with the semantics of a progress bar. ",
                "Its value is a ",
                y.code["Pct"],
                ", e.g. ",
                y.code["Pct.clamp(done / total)"],
                "; texts above and below are optional. For a value the user sets, use the ",
                y.code["slider"],
                ".",
            ],
            showcase(),
        ]
    )
