"""Meta demo page.

A line of metadata whose items are separated by a dot drawn in CSS: the same
look everywhere, skipped by screen readers, and kept at the end of a line
when it wraps.
"""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.page("/meta", title="Meta")
async def meta_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Meta"],
            y.p[
                y.code["meta"],
                " renders a line of metadata — dates, counts, identifiers — ",
                "separated by a dot. The dot comes from CSS, so it looks the same ",
                "everywhere and screen readers skip it. The line takes the font ",
                "size and colour of where it is placed.",
            ],
            y.h2["Basic"],
            c.example(
                # docs:start basic
                c.meta("Eingang 15.03.2026", "12 Seiten", "1 Feld zu prüfen"),
                # docs:end basic
                code=[
                    ("code", src.text("basic"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Values and links"],
            y.p[
                "An item can be more than text. A ",
                y.code["strong"],
                " inside renders as a slightly darker value instead of bold; ",
                "links stay links.",
            ],
            c.example(
                # docs:start values
                c.meta(
                    ["Fall ", y.strong["IV-2026-0142"]],
                    ["AHV-Nr. ", y.strong["756.1978.0814.05"]],
                    ["Geb. ", y.strong["14.08.1978"], ", 47 Jahre"],
                    y.a(href="#")["Im Original prüfen"],
                ),
                # docs:end values
                code=[("code", src.text("values"), "python")],
            ),
            y.h2["In context"],
            y.p[
                "Inside a card it takes the muted style of ",
                y.code["card.subtitle"],
                " or ",
                y.code["card.subtle"],
                ". In a narrow column the line wraps between items and the dot ",
                "stays at the end of the line.",
            ],
            c.example(
                # docs:start context
                c.card(style="max-width: 20rem;")[
                    c.card.header[
                        c.card.title[y.h3["David Meier"]],
                        c.card.subtitle[
                            c.meta("Fall IV-2026-0142", "AHV-Nr. 756.1978.0814.05")
                        ],
                    ],
                    c.card.list[
                        c.card.item[
                            c.card.link(href="#")["Psychiatrisches Gutachten"],
                            c.card.subtle[
                                c.meta(
                                    "Eingang 30.06.2026",
                                    "7 Seiten",
                                    "bereit zum Validieren",
                                )
                            ],
                        ],
                    ],
                ],
                # docs:end context
                code=[("code", src.text("context"), "python")],
            ),
        ],
        width="medium",
    )
