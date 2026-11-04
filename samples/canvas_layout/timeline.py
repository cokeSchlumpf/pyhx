"""The timeline in the canvas design: the course of a dossier in a card.

Included by :mod:`samples.canvas_layout.main`. ``/timeline`` shows a year of a
dossier (documents, appointments, deadlines, payments, notes) with
``c.timeline`` inside a card, as an app on ``CanvasShell`` would place it; every
marker opens its entries in the drawer (``/timeline/entries``), with a pager
when a marker combines several.
"""

from datetime import date, timedelta
from typing import Annotated

import htpy as y
from fastapi import Query

import pyhx.components as c
from pyhx.components import TimelineCategory, TimelineEvent, TimelineQuery
from pyhx.core import WebAppRouter
from pyhx.core.primitives import styles

router = WebAppRouter()

CATEGORIES = [
    TimelineCategory("document", "Documents", "#2563eb", "file-text"),
    TimelineCategory("appointment", "Appointments", "#16a34a", "calendar"),
    TimelineCategory("deadline", "Deadlines", "#d97706", "clock"),
    TimelineCategory("payment", "Payments", "#0d9488", "credit-card"),
    TimelineCategory("note", "Notes", "#64748b", "edit-3", shown=False),
]
_NAMES = {
    "document": "Document",
    "appointment": "Appointment",
    "deadline": "Deadline",
    "payment": "Payment",
    "note": "Note",
}


class _Entry:
    def __init__(self, event: TimelineEvent, title: str, text: str) -> None:
        self.event, self.title, self.text = event, title, text


def _entries() -> list[_Entry]:
    """A year of a dossier: a few busy days, two missed deadlines, payments as periods."""
    out: list[_Entry] = []

    def add(category: str, day: date, title: str, text: str, end: date | None = None, warn: bool = False) -> None:
        label = f"{_NAMES[category]}: {title}, {day:%d %b %Y}"
        out.append(_Entry(TimelineEvent(f"{category}-{len(out)}", category, day, label, end=end, warn=warn), title, text))

    for day, title in [
        (date(2025, 5, 12), "Registration form"),
        (date(2025, 5, 12), "Employer questionnaire"),
        (date(2025, 5, 12), "Medical certificate"),
        (date(2025, 6, 3), "Report of the family doctor"),
        (date(2025, 7, 15), "Hospital report"),
        (date(2025, 7, 15), "Surgery report"),
        (date(2025, 7, 22), "Discharge letter"),
        (date(2025, 9, 8), "Rehabilitation plan"),
        (date(2025, 11, 4), "Report of the specialist"),
        (date(2026, 1, 20), "Questionnaire of the person insured"),
        (date(2026, 3, 16), "Follow-up report"),
        (date(2026, 3, 16), "Second opinion"),
        (date(2026, 4, 15), "Discharge report of the rehabilitation"),
    ]:
        add("document", day, title, "Received and filed in the dossier.")
    for n, day in enumerate(date(2025, 5, 19) + timedelta(days=42 * k) for k in range(9)):
        add("appointment", day, f"Interview {n + 1}", "Interview with the person insured.")
    for day, title, warn in [
        (date(2025, 6, 30), "Documents of the employer due", False),
        (date(2025, 8, 31), "Medical report due", True),
        (date(2025, 12, 15), "Decision on measures due", False),
        (date(2026, 2, 28), "Statement of the person insured due", True),
    ]:
        text = "Missed: no reply by this date." if warn else "Met in time."
        add("deadline", day, title, text, warn=warn)
    for day, end, title in [
        (date(2025, 6, 1), date(2025, 8, 31), "Daily allowance 100 %"),
        (date(2025, 9, 1), date(2025, 12, 31), "Daily allowance 50 %"),
        (date(2026, 1, 1), date(2026, 4, 30), "Daily allowance 50 %"),
    ]:
        add("payment", day, title, "Paid monthly.", end=end)
    for n in range(12):
        add("note", date(2025, 5, 26) + timedelta(days=30 * n), "Case note", "Phone call, summary in the notes.")
    return out


ENTRIES = _entries()
_BY_KEY = {e.event.key: e for e in ENTRIES}


@router.page("/timeline", title="Timeline")
async def timeline_page(
    types: str | None = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Timeline"),
        c.card[
            c.card.header[
                c.card.title[y.h1["Course of the dossier"]],
                c.card.subtitle[
                    "c.timeline in the canvas design: a year of a dossier; missed deadlines pulse in the "
                    "warning colour, payments are periods."
                ],
            ],
            c.card.section[
                c.timeline(
                    [e.event for e in ENTRIES],
                    CATEGORIES,
                    open_url=timeline_entries.url(),
                    shown=types.split(",") if types is not None else None,
                    span=(start, end) if start and end else None,
                    query=TimelineQuery(categories="types", start="from", end="to"),
                    id="dossier-timeline",
                )
            ],
        ],
    ]


@router.fragment.get("/timeline/entries")
async def timeline_entries(key: Annotated[list[str], Query()], index: int = 0) -> y.Node:
    found = [_BY_KEY[k] for k in key if k in _BY_KEY]
    if not found:
        return c.drawer_content(y.p["These entries don't exist anymore."], title="Entries")
    index = max(0, min(index, len(found) - 1))
    entry = found[index]
    event = entry.event

    def at(i: int) -> dict:
        return c.open_drawer_htmx_attributes(timeline_entries.url(query={"key": key, "index": i}), as_dict=True)

    pager = (
        y.span(**styles("flex", "items-center", "gap-sm"))[
            c.button(
                icon="chevron-left",
                aria_label="Previous entry",
                variant="outline",
                size="sm",
                disabled=index == 0,
                **at(index - 1),
            ),
            y.span[f"{index + 1} / {len(found)}"],
            c.button(
                icon="chevron-right",
                aria_label="Next entry",
                variant="outline",
                size="sm",
                disabled=index == len(found) - 1,
                **at(index + 1),
            ),
        ]
        if len(found) > 1
        else None
    )
    when = f"{event.start:%d.%m.%Y}" + (f" – {event.end:%d.%m.%Y}" if event.end else "")
    return c.drawer_content(
        y.div[
            y.p[c.pill(_NAMES[event.category], variant="outline"), " ", when],
            y.h4[entry.title],
            y.p[entry.text],
            c.message("This deadline was missed.", appearance="warning") if event.warn else None,
        ],
        title=_NAMES[event.category] if len(found) == 1 else f"{len(found)} entries",
        header_controls=pager,
    )
