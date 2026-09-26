"""Inline message (alert / callout) demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()


@router.page("/messages", title="Messages")
async def messages_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Messages"],
            y.p[
                "Inline message boxes — soft-tinted alerts that live in the page ",
                "flow. Each renders with a coloured left accent, an optional title, ",
                "body text, an optional leading icon, and an optional close button. ",
                "Unlike ",
                y.a(href="/notifications")["notifications"],
                ", messages sit in the normal layout rather than floating.",
            ],
            y.h2["Appearances"],
            y.p[
                "One ",
                y.code["appearance"],
                " per semantic state.",
            ],
            c.example(
                # docs:start appearances_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message("Here's some information you might find useful.", appearance="info"),
                    c.message("Your changes were saved.", appearance="success"),
                    c.message("You're approaching your monthly quota.", appearance="warning"),
                    c.message("Something went wrong while saving.", appearance="danger"),
                    c.message("A neutral, low-emphasis note.", appearance="neutral"),
                    c.message("A brand-primary highlight.", appearance="primary"),
                ],
                # docs:end appearances_demo
                code=[
                    ("code", src.text("appearances_demo"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Leading icon (optional)"],
            y.p[
                "No icon is shown by default. Pass any ",
                y.code["IconName"],
                " via ",
                y.code["icon="],
                " to add one; it picks up the message's accent colour.",
            ],
            c.example(
                # docs:start icon_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message("Heads up — something to note.", appearance="info", icon="info"),
                    c.message("Your changes were saved.", appearance="success", icon="check-circle"),
                    c.message("Something went wrong.", appearance="danger", icon="alert-octagon"),
                ],
                # docs:end icon_demo
                code=[("code", src.text("icon_demo"), "python")],
            ),
            y.h2["Multiple lines"],
            y.p[
                "With a longer body the icon stays aligned to the first line ",
                "(not the middle of the whole block); single-line messages read ",
                "as vertically centred.",
            ],
            c.example(
                # docs:start multiline_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message(
                        "Single line — the text should sit centred against the icon.",
                        appearance="info",
                        icon="info",
                    ),
                    c.message(
                        y.p(style="margin: 0;")[
                            "This message wraps across several lines so we can check the "
                            "structure. The leading icon is pinned to the first line rather "
                            "than floating to the vertical centre of the whole box, which is "
                            "the conventional behaviour for a longer alert body like this one."
                        ],
                        appearance="warning",
                        icon="alert-triangle",
                    ),
                    c.message(
                        y.p(style="margin: 0;")[
                            "A multi-line message with a title. The title sits on the first "
                            "line next to the icon, and the body flows underneath it across "
                            "as many lines as it needs."
                        ],
                        appearance="success",
                        title="Heads up",
                        icon="check-circle",
                    ),
                ],
                # docs:end multiline_demo
                code=[("code", src.text("multiline_demo"), "python")],
            ),
            y.h2["Title & close button"],
            y.p[
                "Pass ",
                y.code["title="],
                " for a bold heading and ",
                y.code["dismissible=True"],
                " to render an X that removes the message client-side.",
            ],
            c.example(
                # docs:start title_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message(
                        "Review the highlighted fields before continuing.",
                        appearance="warning",
                        title="Check your input",
                        dismissible=True,
                    ),
                    c.message(
                        "This one can be dismissed too.",
                        appearance="info",
                        title="Heads up",
                        dismissible=True,
                    ),
                ],
                # docs:end title_demo
                code=[("code", src.text("title_demo"), "python")],
            ),
            y.h2["Buttons inside a message"],
            y.p[
                "Buttons dropped into a message adopt its appearance colour by ",
                "default — a plain ",
                y.code["button(...)"],
                " (which defaults to ",
                y.code['appearance="neutral"'],
                ") is re-themed to match. A button with an explicit non-neutral ",
                y.code["appearance"],
                " keeps its own colour.",
            ],
            c.example(
                # docs:start buttons_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message(
                        y.div[
                            "A new version is ready to install.",
                            c.button_group(
                                # Default button → adopts the success colour.
                                c.button("Install"),
                                # Ghost secondary action (also adopts, low emphasis).
                                c.button("Later", variant="ghost"),
                                style="margin-top: 0.75rem;",
                            ),
                        ],
                        appearance="success",
                        title="Update available",
                    ),
                    c.message(
                        y.div[
                            "This action cannot be undone.",
                            c.button_group(
                                # Default button → adopts the danger colour.
                                c.button("Delete"),
                                # Explicit appearance → keeps its own (primary) colour.
                                c.button("Keep", appearance="primary", variant="outline"),
                                style="margin-top: 0.75rem;",
                            ),
                        ],
                        appearance="danger",
                        title="Delete item",
                    ),
                    c.message(
                        y.div[
                            "Your session will expire soon. Save your work to avoid "
                            "losing changes.",
                            c.button_group(
                                # Default button → adopts the warning colour.
                                c.button("Stay signed in"),
                                # Ghost secondary action (also adopts, low emphasis).
                                c.button("Log out", variant="ghost"),
                                style="margin-top: 0.75rem;",
                            ),
                        ],
                        appearance="warning",
                        title="Session expiring",
                        icon="clock",
                    ),
                ],
                # docs:end buttons_demo
                code=[("code", src.text("buttons_demo"), "python")],
            ),
            y.h2["Links"],
            y.p[
                "Inline links inside a message adopt its accent colour too, so ",
                "they stay legible against the tinted background.",
            ],
            c.example(
                # docs:start links_demo
                y.div(style="display: flex; flex-direction: column; gap: 0.75rem;")[
                    c.message(
                        y.span[
                            "We couldn't process your payment. ",
                            y.a(href="#")["Update your billing details"],
                            " to try again.",
                        ],
                        appearance="danger",
                        icon="alert-octagon",
                    ),
                    c.message(
                        y.span[
                            "Your export is ready. ",
                            y.a(href="#")["Download the file"],
                            " before it expires.",
                        ],
                        appearance="success",
                        icon="check-circle",
                    ),
                ],
                # docs:end links_demo
                code=[("code", src.text("links_demo"), "python")],
            ),
            y.h2["Example calls"],
            c.code([
                ("code", src.text("example_calls"), "python"),
                ("imports", src.text("imports"), "python"),
            ]),
        ]
    )


# ---------------------------------------------------------------------------
# Fenced source region used only as a code-block source (not a live demo).
# ---------------------------------------------------------------------------

# docs:start example_calls
# c.message("Your changes were saved.", appearance="success")
# c.message("Check your input.", appearance="warning", title="Heads up")
# c.message("Heads up.", appearance="info", icon="info")  # optional icon
# c.message("Delete this item?", appearance="danger", dismissible=True)
# c.message(
#     y.div[
#         "A new version is ready.",
#         c.button("Install"),                      # adopts the message appearance
#         c.button("Later", appearance="primary"),  # keeps its own colour
#     ],
#     appearance="info",
#     title="Update available",
# )
# docs:end example_calls
