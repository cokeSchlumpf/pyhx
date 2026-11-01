"""Main navigation of the Canvas Shell: tabs and sidebar.

Included by :mod:`samples.canvas_layout.main`. Two kinds of pages next to
the plain canvas pages of the sample (no navigation, as before):

- ``/cases``, ``/inbox``, ``/reports`` — the app's areas as **tabs** below the
  top bar (``main_navigation="tabs"``, slot ``main``); the group "Mehr" opens
  as a dropdown.
- ``/admin/...`` — admin pages with a **sidebar** on the canvas
  (``main_navigation="sidebar"``, slot ``admin``), items in labelled groups.
  ``/admin/audit`` shows the sidebar in ``mode="full"``.

The navigation is chosen per page via ``PageResponse(page_template=...)``.
"""

import htpy as y

import pyhx.components as c
from pyhx.core import PageResponse, WebApp, WebAppRouter
from pyhx.page_templates import CanvasShell, CanvasShellMode
from pyhx.utils import lorem_ipsum

from .header import header_content

router = WebAppRouter()


def _tabs(node: y.Node) -> PageResponse:
    return PageResponse(
        node=node,
        page_template=CanvasShell(
            header_content=header_content, main_navigation="tabs"
        ),
    )


def _admin(node: y.Node, mode: CanvasShellMode = "centered") -> PageResponse:
    return PageResponse(
        node=node,
        page_template=CanvasShell(
            header_content=header_content,
            main_navigation="sidebar",
            navigation_slot="admin",
            mode=mode,
        ),
    )


def _variants() -> y.Node:
    return c.card.list[
        [
            c.card.item[
                c.card.link(href=href)[title],
                c.card.subtle[text],
                c.icon("arrow-right-2"),
            ]
            for href, title, text in (
                (
                    "/",
                    "Ohne Navigation",
                    "CanvasShell() — wie bisher, z. B. Dossier-Ansichten",
                ),
                (
                    "/cases",
                    "Tabs",
                    'main_navigation="tabs" — wenige Hauptbereiche der App',
                ),
                (
                    "/admin",
                    "Sidebar",
                    'main_navigation="sidebar" — viele Punkte in Gruppen, Admin',
                ),
                (
                    "/admin/audit",
                    "Sidebar, mode full",
                    "Sidebar am Rand, Inhalt ohne Padding",
                ),
            )
        ]
    ]


def _table(*rows: tuple[str, ...], head: tuple[str, ...]) -> y.Node:
    # Scrolls on its own on a phone instead of widening the page.
    return y.div(style="overflow-x: auto;")[
        y.table[
            y.thead[y.tr[[y.th[h] for h in head]]],
            y.tbody[[y.tr[[y.td[v] for v in row]] for row in rows]],
        ]
    ]


# --- Tabs ---


@router.page("/cases", title="Dossiers")
async def cases() -> PageResponse:
    return _tabs(
        y.div[
            c.breadcrumbs("Dossiers"),
            c.card[
                c.card.header[
                    c.card.title[y.h1["Meine Dossiers"]],
                    c.pill("3", appearance="neutral", size="sm"),
                    c.card.actions[c.button("Neues Dossier", appearance="primary")],
                ],
                c.card.list[
                    [
                        c.card.item[
                            c.icon("document", circle=True, appearance=appearance),
                            c.card.link(href="#")[name],
                            c.card.subtle[c.meta(case, status)],
                            c.icon("arrow-right-2"),
                        ]
                        for name, case, status, appearance in (
                            ("David Meier", "IV-2026-0142", "Neuer Eingang", "success"),
                            ("Anna Keller", "IV-2026-0131", "Abweichungen", "danger"),
                            ("Marco Rossi", "IV-2026-0119", "In Abklärung", "info"),
                        )
                    ]
                ],
            ],
            c.card[
                c.card.header[c.card.title[y.h2["Varianten"]]],
                _variants(),
            ],
        ]
    )


@router.page("/inbox", title="Eingang")
async def inbox() -> PageResponse:
    return _tabs(
        y.div[
            c.breadcrumbs("Eingang"),
            c.card[
                c.card.header[c.card.title[y.h1["Eingang"]]],
                c.card.section[lorem_ipsum(paragraphs=8)],
            ],
        ]
    )


@router.page("/reports", title="Auswertungen")
async def reports() -> PageResponse:
    return _tabs(
        y.div[
            c.breadcrumbs("Auswertungen"),
            c.card[
                c.card.header[c.card.title[y.h1["Auswertungen"]]],
                c.card.section[lorem_ipsum(paragraphs=2)],
            ],
        ]
    )


@router.page("/templates", title="Vorlagen")
async def templates() -> PageResponse:
    return _tabs(
        y.div[
            c.breadcrumbs(y.a(href="/cases")["Mehr"], "Vorlagen"),
            c.card[
                c.card.header[c.card.title[y.h1["Vorlagen"]]],
                c.card.section[
                    y.p["Ein Punkt aus der Gruppe „Mehr“ (Dropdown in den Tabs)."]
                ],
            ],
        ]
    )


@router.page("/archive", title="Archiv")
async def archive() -> PageResponse:
    return _tabs(
        y.div[
            c.breadcrumbs(y.a(href="/cases")["Mehr"], "Archiv"),
            c.card[
                c.card.header[c.card.title[y.h1["Archiv"]]],
                c.card.section[lorem_ipsum(paragraphs=1)],
            ],
        ]
    )


# --- Admin (sidebar) ---


@router.page("/admin", title="Übersicht")
async def admin() -> PageResponse:
    return _admin(
        y.div[
            c.breadcrumbs("Administration"),
            c.card[
                c.card.header[
                    c.card.title[y.h1["Administration"]],
                    c.card.subtitle[
                        "Admin-Seiten mit Sidebar im Slot „admin“; ",
                        "die Tabs der App gibt es hier nicht.",
                    ],
                ],
                _variants(),
            ],
        ]
    )


@router.page("/admin/users", title="Benutzer")
async def admin_users() -> PageResponse:
    return _admin(
        y.div[
            c.breadcrumbs(y.a(href="/admin")["Administration"], "Benutzer"),
            c.card[
                c.card.header[
                    c.card.title[y.h1["Benutzer"]],
                    c.pill("4", appearance="neutral", size="sm"),
                    c.card.actions[c.button("Einladen", appearance="primary")],
                ],
                c.card.section[
                    _table(
                        ("Corinne Baumgartner", "Sachbearbeitung", "aktiv"),
                        ("Daniel Keller", "Medizinischer Dienst", "aktiv"),
                        ("Lea Brunner", "Administration", "aktiv"),
                        ("Tim Huber", "Sachbearbeitung", "eingeladen"),
                        head=("Name", "Rolle", "Status"),
                    )
                ],
            ],
        ]
    )


def _admin_placeholder(title: str) -> PageResponse:
    return _admin(
        y.div[
            c.breadcrumbs(y.a(href="/admin")["Administration"], title),
            c.card[
                c.card.header[c.card.title[y.h1[title]]],
                c.card.section[lorem_ipsum(paragraphs=3)],
            ],
        ]
    )


@router.page("/admin/roles", title="Rollen")
async def admin_roles() -> PageResponse:
    return _admin_placeholder("Rollen")


@router.page("/admin/teams", title="Teams")
async def admin_teams() -> PageResponse:
    return _admin_placeholder("Teams")


@router.page("/admin/settings", title="Einstellungen")
async def admin_settings() -> PageResponse:
    return _admin_placeholder("Einstellungen")


@router.page("/admin/integrations", title="Integrationen")
async def admin_integrations() -> PageResponse:
    return _admin_placeholder("Integrationen")


@router.page("/admin/audit", title="Audit-Log")
async def admin_audit() -> PageResponse:
    pane = "margin: 0; border-radius: 0; min-height: calc(100dvh - 3.5rem);"
    return _admin(
        y.article(style=pane)[
            y.h1["Audit-Log"],
            y.p["Sidebar in mode full: am Rand, der Inhalt ohne Padding."],
            _table(
                *[
                    (f"01.11.2026 09:{m:02d}", "Lea Brunner", "Rolle geändert")
                    for m in range(0, 60, 4)
                ],
                head=("Zeit", "Benutzer", "Aktion"),
            ),
        ],
        mode="full",
    )


# --- Navigation ---


def register_navigation(hx: WebApp) -> None:
    """Menus of the two slots: tabs in ``main``, sidebar in ``admin``."""
    hx.navigation.set(
        {
            "": [
                hx.nav_item(cases),
                hx.nav_item(inbox),
                hx.nav_item(reports),
            ],
            "Mehr": [
                hx.nav_item(templates, icon="file-text"),
                hx.nav_item(archive, icon="archive"),
            ],
        }
    )

    hx.navigation.set(
        {
            "": [hx.nav_item(admin, icon="home", full_match=True)],
            "Benutzer & Zugriff": [
                hx.nav_item(admin_users, icon="users"),
                hx.nav_item(admin_roles, icon="shield"),
                hx.nav_item(admin_teams, icon="user-check"),
            ],
            "System": [
                hx.nav_item(admin_settings, icon="settings"),
                hx.nav_item(admin_integrations, icon="link"),
                hx.nav_item(admin_audit, icon="list"),
            ],
        },
        slot="admin",
    )
