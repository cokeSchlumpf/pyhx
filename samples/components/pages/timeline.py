"""Timeline demo page: a product's year with releases, incidents, sprints, meetings and milestones.

Every marker opens the drawer through the fragment route ``/timeline/events``,
which answers with ``drawer_content`` and a pager for markers that combine
several events.
"""

from datetime import date, timedelta
from typing import Annotated

import htpy as y
from fastapi import Query

# docs:start imports
import pyhx.components as c
from pyhx.components import TimelineCategory, TimelineEvent, TimelineQuery

# docs:end imports
from pyhx.core import WebAppRouter
from pyhx.core.primitives import styles
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()


# docs:start categories
CATEGORIES = [
    TimelineCategory("release", "Releases", "#16a34a", "tag"),
    TimelineCategory("incident", "Incidents", "#dc2626", "zap"),
    TimelineCategory("milestone", "Milestones", "#7c3aed", "flag"),
    TimelineCategory("sprint", "Sprints", "#2563eb", "repeat", shown=False),
    TimelineCategory("meeting", "Meetings", "#64748b", "users", shown=False),
]
# docs:end categories

_NAMES = {
    "release": "Release",
    "incident": "Incident",
    "milestone": "Milestone",
    "sprint": "Sprint",
    "meeting": "Meeting",
}


class _Sample:
    """An event of the sample with its title and the text its drawer shows."""

    def __init__(self, event: TimelineEvent, title: str, text: str) -> None:
        self.event, self.title, self.text = event, title, text


def _sample() -> list[_Sample]:
    """A year of events of a product team."""
    out: list[_Sample] = []

    def add(
        category: str,
        day: date,
        title: str,
        text: str,
        end: date | None = None,
        warn: bool = False,
    ) -> None:
        label = f"{_NAMES[category]}: {title}, {day:%d %b %Y}"
        event = TimelineEvent(f"{category}-{len(out)}", category, day, label, end=end, warn=warn)
        out.append(_Sample(event, title, text))

    start = date(2025, 9, 1)
    for n in range(26):
        first = start + timedelta(days=14 * n)
        add("sprint", first, f"Sprint {n + 1}", "Two weeks of planned work.", end=first + timedelta(days=13))
    for n in range(17):
        add("release", start + timedelta(days=4 + 21 * n), f"Version 3.{n}", "Rolled out to all customers.")
    for n in range(48):
        add("meeting", start + timedelta(days=2 + 7 * n), "Weekly review", "Status, risks and decisions.")
    for day, title, warn in [
        (date(2025, 10, 14), "Slow search", False),
        (date(2025, 11, 3), "Outage of the API", True),
        (date(2025, 12, 22), "Failed nightly import", False),
        (date(2026, 2, 9), "Login errors", True),
        (date(2026, 3, 16), "Payment provider down", True),
        (date(2026, 3, 16), "Queue backlog", False),
        (date(2026, 3, 17), "Mail delays", False),
        (date(2026, 6, 2), "Certificate expired", True),
    ]:
        add("incident", day, title, "Found by the monitoring; the post-mortem is attached.", warn=warn)
    for day, title in [
        (date(2025, 9, 15), "Kick-off"),
        (date(2025, 12, 1), "Beta"),
        (date(2026, 3, 16), "Launch"),
        (date(2026, 7, 1), "One year of the team"),
    ]:
        add("milestone", day, title, "Agreed with the steering committee.")
    return out


SAMPLE = _sample()
_BY_KEY = {s.event.key: s for s in SAMPLE}


@router.page("/timeline", title="Timeline")
async def timeline_page(
    types: str | None = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> y.Node:
    shown = types.split(",") if types is not None else None
    span = (start, end) if start and end else None
    return c.container(
        y.article[
            y.h1["Timeline"],
            y.p[
                "Dated events on a horizontal axis. The units follow the shown span and the width; ",
                "events whose icons would overlap are combined into one marker. Chips choose the ",
                "categories, the slider the span; a marker opens its events in the drawer.",
            ],
            y.h2["A product's year"],
            y.p[
                "Sprints and meetings are hidden by default; flagged incidents draw their marker in the ",
                "warning colour; sprints are periods, drawn as bars along the axis. The chosen categories ",
                "and span are kept in the URL (",
                y.code["?types=…&from=…&to=…"],
                ").",
            ],
            c.example(
                # docs:start timeline
                c.timeline(
                    [s.event for s in SAMPLE],
                    CATEGORIES,
                    open_url=timeline_events.url(),
                    shown=shown,
                    span=span,
                    query=TimelineQuery(categories="types", start="from", end="to"),
                    id="product-year",
                ),
                # docs:end timeline
                code=[
                    ("timeline", src.text("timeline"), "python"),
                    ("categories", src.text("categories"), "python"),
                    ("event", src.text("event"), "python"),
                    ("drawer", src.text("drawer"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["How it works"],
            y.ul[
                y.li[
                    y.code["TimelineEvent"],
                    ": a key, a category, a start and an accessible label; optionally an ",
                    y.code["end"],
                    " (drawn as a bar along the axis) and ",
                    y.code["warn"],
                    " (the warning colour).",
                ],
                y.li[
                    y.code["TimelineCategory"],
                    ": one chip and the look of its markers (colour, icon); ",
                    y.code["shown"],
                    " says whether it is shown by default.",
                ],
                y.li[
                    y.code["open_url"],
                    ": requested with the keys of a marker's events (",
                    y.code["?key=a&key=b"],
                    ") into the drawer; answer with ",
                    y.code["drawer_content"],
                    ". A marker that combines events gets a pager in the drawer's header.",
                ],
                y.li[
                    y.code["query"],
                    ": the parameter names the timeline writes its state to; read them on the server and ",
                    "pass them as ",
                    y.code["shown"],
                    " and ",
                    y.code["span"],
                    ", so a reload shows the same view.",
                ],
                y.li[
                    "Keyboard: Tab reaches chips, markers (in time order) and the slider's thumbs; Enter ",
                    "opens a marker, Esc closes the drawer and returns to the marker.",
                ],
            ],
        ]
    )


# docs:start drawer
@router.fragment.get("/timeline/events")
async def timeline_events(key: Annotated[list[str], Query()], index: int = 0) -> y.Node:
    found = [_BY_KEY[k] for k in key if k in _BY_KEY]
    if not found:
        return c.drawer_content(y.p["These events don't exist anymore."], title="Events")
    index = max(0, min(index, len(found) - 1))
    sample = found[index]
    event = sample.event

    def at(i: int) -> dict:
        return c.open_drawer_htmx_attributes(
            timeline_events.url(query={"key": key, "index": i}), as_dict=True
        )

    pager = (
        y.span(**styles("flex", "items-center", "gap-sm"))[
            c.button(
                icon="chevron-left",
                aria_label="Previous event",
                variant="outline",
                size="sm",
                disabled=index == 0,
                **at(index - 1),
            ),
            y.span[f"{index + 1} / {len(found)}"],
            c.button(
                icon="chevron-right",
                aria_label="Next event",
                variant="outline",
                size="sm",
                disabled=index == len(found) - 1,
                **at(index + 1),
            ),
        ]
        if len(found) > 1
        else None
    )
    when = f"{event.start:%d %b %Y}" + (f" – {event.end:%d %b %Y}" if event.end else "")
    return c.drawer_content(
        y.div[
            y.p[c.pill(_NAMES[event.category], variant="outline"), " ", when],
            y.h4[sample.title],
            y.p[sample.text],
            c.message("Flagged: this incident affected customers.", appearance="warning")
            if event.warn
            else None,
        ],
        title=_NAMES[event.category] if len(found) == 1 else f"{len(found)} events",
        header_controls=pager,
    )


# docs:end drawer

# docs:start event
EXAMPLE = TimelineEvent(
    "incident-7",
    "incident",
    date(2026, 3, 16),
    "Incident: Payment provider down, 16 Mar 2026",
    warn=True,
)
# docs:end event
