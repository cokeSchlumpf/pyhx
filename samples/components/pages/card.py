"""Card demo page.

A card is built by composition from ``card``'s parts: header (title, subtle
text, subtitle, actions), sections with labels, lists of rows, footer. The
CSS places the parts and draws the thin lines between them. This sample runs
in AppShell (default design: bordered card); see ``samples/canvas_layout``
for the canvas design.
"""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.page("/card", title="Card")
async def card_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Card"],
            y.p[
                "A ",
                y.code["card"],
                " is a box built by composition: put its parts in, and the CSS ",
                "places them. Consecutive parts are separated by a thin line.",
            ],
            y.h2["Header"],
            y.p[
                y.code["card.subtle"],
                " stays on the title line and wraps below when space runs out; ",
                y.code["card.subtitle"],
                " always goes to a second line; ",
                y.code["card.actions"],
                " sit on the right. Their order in the header does not matter.",
            ],
            c.example(
                # docs:start header
                c.card[
                    c.card.header[
                        c.card.title[y.h3["Zusammenfassung"]],
                        c.card.subtle["Jeder Satz mit Quelle"],
                        c.card.subtitle["Aktualisiert am 15.03.2026, 09:41 Uhr"],
                        c.card.actions[c.button("Bearbeiten", size="sm")],
                    ],
                    c.card.section[y.p["Card content."]],
                ],
                # docs:end header
                code=[
                    ("code", src.text("header"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Sections and labels"],
            y.p[
                y.code["card.section"],
                " is a padded block; ",
                y.code["card.label"],
                " is the small heading inside it. Wrap a heading in it to keep ",
                "the document outline.",
            ],
            c.example(
                # docs:start sections
                c.card[
                    c.card.header[c.card.title[y.h3["Dossier"]]],
                    c.card.section[
                        c.card.label["Angabe in der Anmeldung"],
                        y.p["AU 100% seit 20.01.2026"],
                    ],
                    c.card.section[
                        c.card.label[y.h4["Ausgangslage"]],
                        y.p["Anmeldung bei der IV am 15.03.2026."],
                        c.card.label[y.h4["Gesundheit"]],
                        y.p["Depression mit Erschöpfung und Schlafstörungen."],
                    ],
                ],
                # docs:end sections
                code=[("code", src.text("sections"), "python")],
            ),
            y.h2["Clickable rows"],
            y.p[
                "In a ",
                y.code["card.list"],
                ", an item with a ",
                y.code["card.link"],
                " or ",
                y.code["card.button"],
                " is clickable as a whole: the element stretches an invisible ",
                "overlay across the row, no JavaScript. Other links in the row ",
                "(here: the source) stay clickable on their own.",
            ],
            c.example(
                # docs:start list
                c.card[
                    c.card.header[c.card.title[y.h3["Dokumente"]]],
                    c.card.list[
                        c.card.item[
                            c.card.link(href="#")["IV-Anmeldung 001.001"],
                            c.card.subtle["Eingang 15.03.2026 · 12 Seiten"],
                        ],
                        c.card.item[
                            c.card.button["Beginn AU prüfen"],
                            c.card.subtle[
                                "Unsicher gelesen · ",
                                y.a(href="#")["Anmeldung S. 6"],
                            ],
                        ],
                        c.card.item[
                            c.card.label["Tätigkeit"],
                            y.span["Bauleiter (not clickable)"],
                        ],
                    ],
                ],
                # docs:end list
                code=[("code", src.text("list"), "python")],
            ),
            y.h2["Footer"],
            c.example(
                # docs:start footer
                c.card[
                    c.card.header[c.card.title[y.h3["Vorschlag"]]],
                    c.card.section[y.p["AU 100% seit 20.01.2026 übernehmen?"]],
                    c.card.footer[
                        c.button("Verwerfen"),
                        c.button("Übernehmen", appearance="primary"),
                    ],
                ],
                # docs:end footer
                code=[("code", src.text("footer"), "python")],
            ),
            y.h2["Collapsible"],
            y.p[
                "Passing ",
                y.code["open"],
                " makes the card collapsible: the header becomes the toggle of ",
                "a native ",
                y.code["<details>"],
                ". It must come first and should not contain actions.",
            ],
            c.example(
                # docs:start collapsible
                c.card(open=False)[
                    c.card.header[
                        c.card.title[y.h3["Extrahierte Angaben"]],
                        c.card.subtle["Je mit Quelle und Seite"],
                    ],
                    c.card.list[
                        c.card.item[c.card.label["Tätigkeit"], y.span["Bauleiter"]],
                        c.card.item[c.card.label["Pensum"], y.span["100%"]],
                    ],
                ],
                c.card(open=True)[
                    c.card.header[c.card.title[y.h3["Verlauf"]]],
                    c.card.section[y.p["Open on load."]],
                ],
                # docs:end collapsible
                code=[("code", src.text("collapsible"), "python")],
            ),
        ],
        width="medium",
    )
