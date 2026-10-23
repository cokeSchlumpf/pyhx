"""Canvas Shell layout sample.

Run with::

    poetry run fastapi dev samples/canvas_layout/main.py

One page per ``CanvasShell`` mode (``centered``, ``wide``, ``full``), each with
breadcrumbs and placeholder content, plus a dossier page built from
``card``s in a ``split_layout`` (main column and sticky aside below the
breadcrumbs). The panes of the ``full`` page are plain Pico ``<article>``
placeholders, since a document viewer has panes, not cards.
"""

from typing import get_args

import htpy as y
import pyhx.components as c

from pyhx.components.variants import Appearance
from pyhx.core import PageResponse, RequestContext, WebApp
from pyhx.page_templates import CanvasShell
from pyhx.utils import lorem_ipsum


def header_content() -> y.Node:
    """Evaluated per request: shows the current user next to a static label.

    The shell draws the separator line between the direct children.
    """
    return [
        y.span["Muster AG"],
        y.span[RequestContext.get().user.display_name],
    ]


hx = WebApp(
    title="Canvas Layout",
    default_page_template=CanvasShell(header_content=header_content),
)


def _modes() -> y.Node:
    return y.ul[
        y.li[y.a(href="/")["centered"], " — at most 72rem, the default"],
        y.li[y.a(href="/wide")["wide"], " — at most --hx-container-width-wide"],
        y.li[y.a(href="/full")["full"], " — full width, no padding"],
        y.li[y.a(href="/dossier")["dossier"], " — split layout with a sticky aside"],
        y.li[y.a(href="/colors")["colors"], " — appearance colours of the design"],
    ]


@hx.page("/", title="Centered")
async def centered() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Centered"),
        c.card[
            c.card.header[c.card.title[y.h1["Centered"]]],
            c.card.section[
                y.p["The content column is centered and at most 72rem wide."],
                _modes(),
            ],
        ],
        c.card[c.card.section[lorem_ipsum(paragraphs=12)]],
    ]


@hx.page("/wide", title="Wide")
async def wide() -> PageResponse:
    return PageResponse(
        node=y.div[
            c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Wide"),
            c.card[
                c.card.header[c.card.title[y.h1["Wide"]]],
                c.card.section[
                    y.p["Same design, wider content column — e.g. for wide tables."],
                    _modes(),
                ],
            ],
            c.card[c.card.section[lorem_ipsum(paragraphs=4)]],
        ],
        page_template=CanvasShell(header_content=header_content, mode="wide"),
    )


@hx.page("/full", title="Full")
async def full() -> PageResponse:
    pane = "margin: 0; border-radius: 0; min-height: calc(100dvh - 3.5rem);"
    return PageResponse(
        node=y.div(
            style="display: grid; grid-template-columns: 12rem 1fr 24rem; gap: 1px;"
        )[
            y.article(style=pane)["Thumbnails"],
            y.article(style=pane)[
                y.h1["Full"],
                y.p["Full viewport width without padding, e.g. a document viewer."],
                _modes(),
            ],
            y.article(style=pane)["Extracted values"],
        ],
        page_template=CanvasShell(header_content=header_content, mode="full"),
    )


def _action_needed() -> y.Node:
    """Aside card with fixed groups and a collapsible "Erledigt" group."""

    def item(title: str, *details: y.Node) -> y.Node:
        return c.card.item[
            c.card.link(href="#")[title],
            c.card.subtle[c.meta(*details)],
        ]

    return c.card[
        c.card.header[
            c.card.title[y.h2["Handlungsbedarf"]],
            c.pill("4", appearance="warning", size="sm"),
        ],
        c.card.group[
            c.card.label[y.h3["Neues Dokument 1"]],
            c.card.list[
                item(
                    "Psychiatrisches Gutachten",
                    "Eingang 30.06.2026",
                    "7 Seiten",
                    "bereit zum Validieren",
                ),
            ],
        ],
        c.card.group[
            c.card.label[y.h3["Abweichungen 2"]],
            c.card.list[
                item("Diagnose", "Dr. Keller F33.2", "Gutachten F32.1"),
                item(
                    "Funktionsniveau",
                    "Dr. Keller Konzentration etwa 30 Minuten",
                    "Arbeitgeber zweistündige Besprechung",
                ),
            ],
        ],
        c.card.group[
            c.card.label[y.h3["Lücke 1"]],
            c.card.list[
                item(
                    "Keine Arbeitsunfähigkeitszeugnisse im Dossier",
                    "15.03. bis 01.04.2026",
                ),
            ],
        ],
        c.card.group(open=False)[
            c.card.header[
                c.card.title[y.h3["Erledigt"]],
                c.pill("4", appearance="neutral", size="sm"),
            ],
            c.card.list[
                item("IV-Anmeldung validiert", "15.03.2026"),
                item("Arztbericht angefordert", "18.03.2026"),
                item("Beginn AU geprüft", "20.03.2026"),
                item("Arbeitgeberfragebogen erhalten", "02.04.2026"),
            ],
        ],
    ]


@hx.page("/dossier", title="Dossier")
async def dossier() -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Meine Dossiers"], "IV-2026-0142"),
        c.split_layout(
            main=y.fragment[
                c.card[
                    c.card.header[
                        c.card.title[y.h1["David Meier"]],
                        c.pill(
                            "Neuer Eingang", appearance="success", variant="outline"
                        ),
                        c.card.subtitle[
                            c.meta(
                                ["Fall ", y.strong["IV-2026-0142"]],
                                ["AHV-Nr. ", y.strong["756.1978.0814.05"]],
                                ["Geb. ", y.strong["14.08.1978"], ", 47 Jahre"],
                            )
                        ],
                        c.card.actions[c.button("Bearbeiten")],
                    ],
                ],
                c.card[
                    c.card.header[
                        c.card.title[y.h2["Zusammenfassung"]],
                        c.card.subtitle[
                            "Aktualisiert am 15.03.2026, 09:41 Uhr, nach Eingang ",
                            "IV-Anmeldung 001.001. Jeder Satz mit Quelle.",
                        ],
                    ],
                    c.card.section[
                        c.card.label["Angabe in der Anmeldung"],
                        y.p["AU 100% seit 20.01.2026"],
                    ],
                    c.card.section[
                        c.card.label[y.h3["Ausgangslage"]],
                        y.p[
                            "Herr David Meier, Bauleiter bei der Muster Bau AG, ",
                            "meldete sich am 15.03.2026 bei der IV an.",
                        ],
                        c.card.label[y.h3["Gesundheit"]],
                        y.p[
                            "Als gesundheitliche Beeinträchtigung nennt die Anmeldung ",
                            "eine Depression mit Erschöpfung und Schlafstörungen.",
                        ],
                        c.card.label[y.h3["Erwerb"]],
                        y.p[
                            "Herr Meier ist seit 2014 bei der Muster Bau AG als ",
                            "Bauleiter tätig, mit einem Pensum von 100%.",
                        ],
                    ],
                    c.card.footer[
                        c.button("Verwerfen"),
                        c.button("Übernehmen", appearance="primary"),
                    ],
                ],
                c.card(open=False)[
                    c.card.header[
                        c.card.title[y.h2["Extrahierte Angaben"]],
                        c.pill("4", appearance="neutral", size="sm"),
                        c.card.subtle[
                            "Im Dokument attestiert oder angegeben, ",
                            "je mit Quelle und Seite",
                        ],
                    ],
                    c.card.list[
                        [
                            c.card.item[
                                c.card.label[label],
                                y.span[value],
                                c.card.subtle[
                                    y.a(href="#")[source],
                                ],
                            ]
                            for label, value, source in (
                                ("Tätigkeit", "Bauleiter", "Anmeldung S. 9"),
                                ("Pensum", "100%", "Anmeldung S. 9"),
                                ("Beginn AU", "20.01.2026", "Anmeldung S. 6"),
                                ("Grad AU", "100%", "Anmeldung S. 6"),
                            )
                        ]
                    ],
                ],
                c.card[
                    c.card.header[
                        c.card.title[y.h2["Dokumente"]],
                        c.pill("2", appearance="neutral", size="sm"),
                    ],
                    c.card.list[
                        c.card.item[
                            c.card.link(href="#")["IV-Anmeldung 001.001"],
                            c.card.subtle[c.meta("Eingang 15.03.2026", "12 Seiten")],
                        ],
                        c.card.item[
                            c.card.link(href="#")["Arztbericht Dr. Keller"],
                            c.card.subtle[
                                c.meta(
                                    "Eingang 22.03.2026",
                                    "4 Seiten",
                                    y.a(href="#")["Quelle öffnen"],
                                )
                            ],
                        ],
                    ],
                ],
                c.card[
                    c.card.header[c.card.title[y.h2["Notizen"]]],
                    c.card.section[lorem_ipsum(paragraphs=6)],
                ],
            ],
            aside=_action_needed(),
        ),
    ]


@hx.page("/colors", title="Colors")
async def colors() -> y.Node:
    """Semantic colours of the canvas design (themes/canvas.css)."""
    appearances: tuple[Appearance, ...] = get_args(Appearance)

    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Colors"),
        c.card[
            c.card.header[
                c.card.title[y.h1["Colors"]],
                c.card.subtitle[
                    "Appearance colours of the canvas design, taken from the draft: ",
                    "success = jade, warning = amber, danger = orange, info = sky.",
                ],
            ],
            c.card.section[
                c.card.label["Pills"],
                c.pill.container(
                    *[c.pill(a, appearance=a) for a in appearances],
                    style="margin-bottom: 0.75rem;",
                ),
                c.pill.container(
                    *[
                        c.pill(a, appearance=a, variant="outline")
                        for a in appearances
                    ],
                    style="margin-bottom: 0.75rem;",
                ),
                c.pill.container(
                    *[c.pill(a, appearance=a, size="sm") for a in appearances],
                ),
            ],
            c.card.section[
                c.card.label["Buttons"],
                c.pill.container(*[c.button(a, appearance=a) for a in appearances]),
            ],
            c.card.section[
                c.card.label["Messages"],
                [
                    c.message(f"A {a} message.", appearance=a, title=a.title())
                    for a in appearances
                ],
            ],
        ],
    ]


app = hx.create_app()
