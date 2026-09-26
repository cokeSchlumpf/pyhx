"""Notification badge demo page."""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()

ROW = "display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;"


@router.page("/notification-badge", title="Notification Badge")
async def notification_badge_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Notification Badge"],
            y.p[
                "Overlays a small count bubble on the top-right corner of whatever ",
                "it wraps. ",
                y.code["count=0"],
                " renders the child alone, with no bubble, so callers don't need ",
                "their own conditional.",
            ],
            y.h2["On buttons"],
            y.p[
                "The three button shapes: icon-only, icon + text, and text-only. ",
                "The bubble is positioned against the wrapper, so it sits on the ",
                "corner regardless of the button's width.",
            ],
            c.example(
                # docs:start buttons
                y.div(style=ROW)[
                    c.notification_badge(
                        c.button(icon="bell", aria_label="Notifications"), count=3
                    ),
                    c.notification_badge(
                        c.button("Todos", icon="check-square"), count=7
                    ),
                    c.notification_badge(c.button("Inbox"), count=12),
                    c.notification_badge(
                        c.button("Ghost", icon="bell", variant="ghost"), count=2
                    ),
                    c.notification_badge(
                        c.button("Small", icon="bell", size="sm"), count=5
                    ),
                    c.notification_badge(
                        c.button("Large", icon="bell", size="lg"), count=5
                    ),
                ],
                # docs:end buttons
                code=[
                    ("code", src.text("buttons"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Counts"],
            y.p[
                "Single digit, double digit, and capped by ",
                y.code["max"],
                " (default 99) so a large number can't stretch the bubble ",
                "indefinitely. ",
                y.code["count=0"],
                " shows the bare child.",
            ],
            c.example(
                # docs:start counts
                y.div(style=ROW)[
                    c.notification_badge(c.button("Zero", icon="bell"), count=0),
                    c.notification_badge(c.button("One", icon="bell"), count=1),
                    c.notification_badge(c.button("Ten", icon="bell"), count=10),
                    c.notification_badge(c.button("Capped", icon="bell"), count=1234),
                    c.notification_badge(
                        c.button("Max 9", icon="bell"), count=42, max=9
                    ),
                ],
                # docs:end counts
                code=[("code", src.text("counts"), "python")],
            ),
            y.h2["On other elements"],
            y.p["Not button-specific — it wraps any node."],
            c.example(
                # docs:start others
                y.div(style=ROW)[
                    c.notification_badge(c.icon("bell"), count=4),
                    c.notification_badge(
                        y.div(
                            style=(
                                "width: 7rem; height: 3rem; display: flex;"
                                "align-items: center; justify-content: center;"
                                "border: 1px solid var(--hx-color-neutral-300);"
                                "border-radius: var(--hx-radius-md);"
                            )
                        )["Plain div"],
                        count=9,
                    ),
                    c.notification_badge(
                        c.pill("Pill", appearance="info"),
                        count=2,
                    ),
                ],
                # docs:end others
                code=[("code", src.text("others"), "python")],
            ),
            y.h2["In a card"],
            y.p[
                "A badged element inside other content, to check the bubble is not ",
                "clipped by a surrounding container.",
            ],
            c.example(
                # docs:start in_card
                c.bubble(appearance="neutral")[
                    y.div(style=ROW)[
                        c.notification_badge(
                            c.button("Messages", icon="mail", variant="outline"),
                            count=3,
                        ),
                        c.notification_badge(c.icon("bell"), count=11),
                        y.span["…alongside ordinary content."],
                    ]
                ],
                # docs:end in_card
                code=[("code", src.text("in_card"), "python")],
            ),
        ]
    )
