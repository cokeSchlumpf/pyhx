"""Chronicle demo page.

Entries in time order: a date on the left, a marker (dot or icon) on a
connecting line, the content on the right. Built by composition, with
``meta`` and ``pill`` inside the entries.
"""

import htpy as y

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.page("/chronicle", title="Chronicle")
async def chronicle_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Chronicle"],
            y.p[
                "A ",
                y.code["chronicle"],
                " lists entries in time order — documents received, steps of a ",
                "case, changes. Each ",
                y.code["chronicle.entry"],
                " has a date on the left, a marker on the line connecting the ",
                "entries, and its content on the right: a ",
                y.code["chronicle.title"],
                ", a line of ",
                y.code["meta"],
                " and a ",
                y.code["chronicle.text"],
                ". All parts are optional.",
            ],
            y.h2["Basic"],
            c.example(
                # docs:start basic
                c.chronicle[
                    c.chronicle.entry(date="12.04.2026")[
                        c.chronicle.title["Arbeitgeberfragebogen Muster Bau AG"],
                        c.meta("Arbeitgeberfragebogen", "Muster Bau AG", "3 Seiten"),
                        c.chronicle.text["Seit 01.04.2026 Einsatz zu 50% (S. 2)"],
                    ],
                    c.chronicle.entry(date="05.04.2026")[
                        c.chronicle.title["Arztbericht Dr. Keller"],
                        c.meta("Arztbericht", "Dr. med. Daniel Keller", "4 Seiten"),
                    ],
                    c.chronicle.entry(date="15.03.2026")[
                        c.chronicle.title["IV-Anmeldung 001.001"],
                    ],
                ],
                # docs:end basic
                code=[
                    ("code", src.text("basic"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
                max_height=None,
            ),
            y.h2["Marker colours"],
            y.p[
                y.code["appearance"],
                " colours the dot like a pill. ",
                y.code["color"],
                " takes any CSS colour instead — e.g. one per document type — ",
                "and wins over ",
                y.code["appearance"],
                ".",
            ],
            c.example(
                # docs:start colours
                c.chronicle[
                    c.chronicle.entry(date="Appearance", appearance="success")[
                        c.chronicle.title["success"],
                    ],
                    c.chronicle.entry(date="Appearance", appearance="danger")[
                        c.chronicle.title["danger"],
                    ],
                    c.chronicle.entry(date="Color", color="#F194B4")[
                        c.chronicle.title["Arbeitgeber (#F194B4)"],
                    ],
                    c.chronicle.entry(date="Color", color="#7EA16B")[
                        c.chronicle.title["Arztbericht (#7EA16B)"],
                    ],
                ],
                # docs:end colours
                code=[("code", src.text("colours"), "python")],
                max_height=None,
            ),
            y.h2["Icons instead of dots"],
            y.p[
                y.code["icon"],
                " shows the icon in a circle instead of the dot (as ",
                y.code["icon(..., circle=True)"],
                "), coloured the same way. Entries with and without icons can be ",
                "mixed: as soon as one entry has an icon, the marker column widens ",
                "for all of them, so the line stays straight.",
            ],
            c.example(
                # docs:start icons
                c.chronicle[
                    c.chronicle.entry(date="17.04.2026", icon="pencil")[
                        c.chronicle.title["Rückfrage an Dr. Keller vorbereitet"],
                        c.meta("S. Brunner", "nicht versendet"),
                    ],
                    c.chronicle.entry(
                        date="14.04.2026", icon="send-2", appearance="info"
                    )[
                        c.chronicle.title["Anfrage an Helvetia versendet"],
                    ],
                    c.chronicle.entry(date="12.04.2026", color="#F194B4")[
                        c.chronicle.title["Arbeitgeberfragebogen eingegangen"],
                    ],
                    c.chronicle.entry(
                        date="15.03.2026", icon="check-2", appearance="success"
                    )[
                        c.chronicle.title["IV-Anmeldung validiert"],
                    ],
                ],
                # docs:end icons
                code=[("code", src.text("icons"), "python")],
                max_height=None,
            ),
            y.h2["Clickable entries"],
            y.p[
                "A link in ",
                y.code["chronicle.title"],
                " stretches an invisible overlay across the whole entry — the ",
                "entry is one link, with hover and focus on the whole row, no ",
                "JavaScript. Other links in the entry (here: the page reference) ",
                "stay clickable on their own. A ",
                y.code["pill"],
                " next to the title marks e.g. new entries.",
            ],
            c.example(
                # docs:start clickable
                c.chronicle[
                    c.chronicle.entry(date="05.04.2026", color="#7EA16B")[
                        c.chronicle.title[
                            y.a(href="#")["Arztbericht Dr. Keller"],
                            c.pill("Neu", appearance="success", variant="outline"),
                        ],
                        c.meta("Arztbericht", "Dr. med. Daniel Keller", "4 Seiten"),
                        c.chronicle.text[
                            "Angepasste Tätigkeit 50% zumutbar ab 01.04.2026 ",
                            y.a(href="#")["(S. 3)"],
                        ],
                    ],
                    c.chronicle.entry(date="15.03.2026", color="#BFD5E2")[
                        c.chronicle.title[y.a(href="#")["IV-Anmeldung 001.001"]],
                        c.meta("Anmeldung", "David Meier", "12 Seiten"),
                    ],
                ],
                # docs:end clickable
                code=[("code", src.text("clickable"), "python")],
                max_height=None,
            ),
            y.h2["In a card"],
            y.p[
                "Put the chronicle directly into a ",
                y.code["card"],
                " — it brings its own padding, and the card draws the line below ",
                "the header.",
            ],
            c.example(
                # docs:start card
                c.card[
                    c.card.header[
                        c.card.title[y.h3["Dokumente"]],
                        c.pill("2", appearance="neutral", size="sm"),
                    ],
                    c.chronicle[
                        c.chronicle.entry(date="05.04.2026", color="#7EA16B")[
                            c.chronicle.title[y.a(href="#")["Arztbericht Dr. Keller"]],
                            c.meta("Arztbericht", "4 Seiten"),
                        ],
                        c.chronicle.entry(date="15.03.2026", color="#BFD5E2")[
                            c.chronicle.title[y.a(href="#")["IV-Anmeldung 001.001"]],
                            c.meta("Anmeldung", "12 Seiten"),
                        ],
                    ],
                ],
                # docs:end card
                code=[("code", src.text("card"), "python")],
                max_height=None,
            ),
        ],
        width="medium",
    )
