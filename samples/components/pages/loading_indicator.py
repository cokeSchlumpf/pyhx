"""Loading indicator demo page.

``showcase()`` renders every kind, size and appearance and the places the
mark is used in, each with its code; the components sample (plain design)
shows it at ``/loading-indicator``, the canvas layout sample at
``/loading-indicators``.
"""

import htpy as y

# docs:start imports
import pyhx.components as c

# docs:end imports
from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()

_KINDS = (
    ("spinner", "A turning arc: wait, it's loading. For short waits, in buttons."),
    ("ripple", "A dot sending out a ring: live, running. Next to a status."),
    ("pulse", "A dot that breathes. The quietest; for dense lists."),
    ("dots", "Three dots in turn. After a word: Saving, Waiting."),
    ("bars", "Three bars rising and falling: working on it. The busiest."),
)

_APPEARANCES = ("primary", "info", "neutral", "success", "warning", "danger")


def _grid(*items: y.Node) -> y.Node:
    # Several columns, fewer at phone width.
    return y.div(
        style="display: grid; gap: 1.25rem 2rem;"
        " grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr));"
    )[items]


def _row(*items: y.Node) -> y.Node:
    # A flex row centred on its line, as a header or a status cell lays out.
    return y.div(
        style="display: flex; flex-wrap: wrap; align-items: center; gap: 0.625rem;"
    )[items]


def _matrix(columns: tuple[str, ...], rows: list[tuple[str, list[y.Node]]]) -> y.Node:
    # A label column and one centred cell per column.
    return y.div(
        style="display: grid; align-items: center; gap: 0.75rem 0.5rem;"
        f" grid-template-columns: 4.5rem repeat({len(columns)}, minmax(0, 1fr));"
    )[
        y.span,
        [y.small(style="text-align: center")[column] for column in columns],
        [
            [
                y.small[name],
                [y.div(style="display: flex; justify-content: center")[cell] for cell in cells],
            ]
            for name, cells in rows
        ],
    ]


def showcase() -> y.Node:
    """The examples of the loading indicator, each with its code."""
    return [
        y.h2["Kinds"],
        y.p[
            "A small mark with no text that says “this is happening right now”. ",
            y.code["kind"],
            " chooses its shape and motion; ",
            y.code["spinner"],
            " is the default. Screen readers announce its ",
            y.code["label"],
            " (",
            y.code['role="status"'],
            "); when the work ends, the app no longer renders it.",
        ],
        c.example(
            _grid(
                *[
                    y.div(style="display: flex; flex-direction: column; gap: 0.5rem")[
                        y.div(
                            style="display: flex; align-items: center;"
                            " justify-content: center; height: 4rem;"
                        )[
                            # docs:start kinds
                            c.loading_indicator(label="Loading", kind=kind, size="lg")
                            # docs:end kinds
                        ],
                        y.strong[kind],
                        y.small[hint],
                    ]
                    for kind, hint in _KINDS
                ]
            ),
            code=[
                ("code", src.text("kinds"), "python"),
                ("imports", src.text("imports"), "python"),
            ],
        ),
        y.h2["Sizes"],
        y.p[
            y.code["size"],
            " sizes the mark to sit beside text: ",
            y.code["sm"],
            " next to 12–13px text and in table rows, ",
            y.code["md"],
            " (the default) next to body text and pills, ",
            y.code["lg"],
            " next to headings.",
        ],
        c.example(
            _matrix(
                ("sm", "md", "lg"),
                [
                    (
                        kind,
                        [
                            # docs:start sizes
                            c.loading_indicator(label="Loading", kind=kind, size=size)
                            # docs:end sizes
                            for size in ("sm", "md", "lg")
                        ],
                    )
                    for kind, _ in _KINDS
                ],
            ),
            code=[("code", src.text("sizes"), "python")],
        ),
        y.h2["Appearances"],
        y.p[
            y.code["appearance"],
            " takes the colours of pills and the progress bar; ",
            y.code["primary"],
            " is the default (in the canvas design the text colour). Inside a solid button the mark takes the button's text colour.",
        ],
        c.example(
            _matrix(
                _APPEARANCES,
                [
                    (
                        kind,
                        [
                            # docs:start appearances
                            c.loading_indicator(
                                label="Loading", kind=kind, appearance=appearance
                            )
                            # docs:end appearances
                            for appearance in _APPEARANCES
                        ],
                    )
                    for kind, _ in _KINDS
                ],
            ),
            code=[("code", src.text("appearances"), "python")],
        ),
        y.h2["In use"],
        y.p[
            "The mark composes with other components; pills, buttons and links stay as they are. ",
            "With reduced motion set in the system, nothing moves: the pulse stays a solid dot, the ripple loses its ring, the spinner shows a half arc, dots and bars stand at a middle step.",
        ],
        y.h3["Next to a status, in a header"],
        y.p["Beside the pill, the pill says what and the mark says “now”; inside the pill, the mark stands before its text."],
        c.example(
            y.div(style="display: grid; gap: 1rem")[
            # docs:start header
            _row(
                y.span(style="font-size: 1.5rem; font-weight: 600")["Quarterly report"],
                c.pill("In progress", appearance="neutral"),
                c.loading_indicator(
                    label="Import running", kind="ripple", appearance="info"
                ),
                c.pill("Import 35 %", appearance="info"),
            ),
            _row(
                y.span(style="font-size: 1.5rem; font-weight: 600")["Quarterly report"],
                c.pill("In progress", appearance="neutral"),
                c.pill(
                    [
                        c.loading_indicator(
                            label="Import running",
                            kind="ripple",
                            appearance="info",
                            size="sm",
                        ),
                        "Import 35 %",
                    ],
                    appearance="info",
                ),
            ),
            # docs:end header
            ],
            code=[("code", src.text("header"), "python")],
        ),
        y.h3["On buttons"],
        y.p[
            "Beside the label of a button that leads to the running work; as a spinner before the label while the button's own action runs. ",
            "Inside a button, the mark's ",
            y.code["label"],
            " becomes part of the button's name: choose one that reads on from the button's text (“Import running”), or give the button its own ",
            y.code["aria_label"],
            ".",
        ],
        c.example(
            # docs:start buttons
            _row(
                c.button("Files · 2", variant="outline"),
                c.button(
                    [
                        "Import",
                        c.loading_indicator(
                            label="running",
                            kind="ripple",
                            appearance="info",
                            size="sm",
                        ),
                    ],
                    variant="outline",
                ),
                c.button(
                    [c.loading_indicator(label="Saving", size="sm"), "Saving"],
                    appearance="primary",
                    aria_label="Saving",
                ),
            ),
            # docs:end buttons
            code=[("code", src.text("buttons"), "python")],
        ),
        y.h3["In a table"],
        y.p["Only rows with work in progress move; finished rows are still."],
        c.example(
            # docs:start table
            y.table[
                y.thead[y.tr[y.th["Document"], y.th["Status"], y.th["Pages"]]],
                y.tbody[
                    y.tr[
                        y.td["statement-2026-09.pdf"],
                        y.td[
                            _row(
                                c.loading_indicator(
                                    label="Being processed",
                                    kind="pulse",
                                    appearance="info",
                                    size="sm",
                                ),
                                "Being processed",
                            )
                        ],
                        y.td["12"],
                    ],
                    y.tr[
                        y.td["statement-2026-10.pdf"],
                        y.td[
                            _row(
                                c.loading_indicator(
                                    label="Waiting",
                                    kind="dots",
                                    appearance="neutral",
                                    size="sm",
                                ),
                                "Waiting",
                            )
                        ],
                        y.td["9"],
                    ],
                    y.tr[
                        y.td["statement-2026-08.pdf"],
                        y.td[c.pill("Done", appearance="success")],
                        y.td["14"],
                    ],
                ],
            ],
            # docs:end table
            code=[("code", src.text("table"), "python")],
        ),
        y.h3["In navigation"],
        y.p["Tells from anywhere in the app that something runs in another section."],
        c.example(
            # docs:start navigation
            y.nav(
                aria_label="Sections",
                style="display: flex; flex-direction: column; gap: 0.5rem",
            )[
                y.a(href="#overview")["Overview"],
                y.a(href="#imports")[
                    "Imports",
                    c.loading_indicator(
                        label="running",
                        kind="ripple",
                        appearance="info",
                        size="sm",
                        style="margin-inline-start: 0.375rem",
                    ),
                ],
                y.a(href="#reports")["Reports"],
            ],
            # docs:end navigation
            code=[("code", src.text("navigation"), "python")],
        ),
    ]


@router.page("/loading-indicator", title="Loading Indicator")
async def loading_indicator_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Loading Indicator"],
            y.p[
                "A ",
                y.code["loading_indicator"],
                " is a small mark that says “this is happening right now”, next to a label, a pill, a button, a table row or a link. ",
                "To show how far the work has got, use the ",
                y.code["progress_bar"],
                ".",
            ],
            showcase(),
        ]
    )
