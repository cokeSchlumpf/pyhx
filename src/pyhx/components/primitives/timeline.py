"""Timeline: dated events on a horizontal axis with an adjustable span.

``timeline(events, categories, open_url=...)`` renders the whole control::

    timeline(
        events=[
            TimelineEvent("e1", "release", date(2026, 3, 2), "Release 2.1, 2 Mar 2026"),
            TimelineEvent("e2", "sprint", date(2026, 3, 2), "Sprint 14", end=date(2026, 3, 13)),
            TimelineEvent("e3", "incident", date(2026, 3, 9), "Outage of the API", warn=True),
        ],
        categories=[
            TimelineCategory("release", "Releases", "#16a34a", "tag"),
            TimelineCategory("sprint", "Sprints", "#2563eb", "repeat", shown=False),
            TimelineCategory("incident", "Incidents", "#dc2626", "zap"),
        ],
        open_url="/timeline/events",
    )

- **Axis.** Ticks in the unit that fits the shown span and the width (years,
  quarters, months, weeks or days), labelled in the page's language.
- **Markers.** Each event is a dot on the axis with a line to a round icon
  above or below it, in one of four places. Events whose icons would overlap
  are combined into one marker that shows their number, so nothing overlaps
  at any width. A marker with a ``warn`` event is drawn in the warning
  colour. An event with an ``end`` also shows as a bar along the axis.
- **Details.** A marker is a button that requests ``open_url`` with the keys
  of its events (``?key=e1&key=e3``) into the drawer, as
  ``open_drawer_htmx_attributes`` does: answer with ``drawer_content``.
- **Filter and span.** Chips toggle the categories, with their number of
  events in the shown span; a range slider over a strip of events per month
  sets the span. Neither needs a request.
- **URL.** With ``query``, the shown categories and span are written into the
  page's URL (``history.replaceState``); read them back on the server and
  pass them as ``shown`` and ``span``.

The server renders the controls and the data; ``pyhx.timeline.js`` lays out
the axis in the browser, since the layout depends on the width.
"""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta

import htpy as y
from markupsafe import Markup

from pyhx.core.primitives import IconName, classnames, merge_styles
from pyhx.i18n import _

from .button import button
from .icon import icon
from .slider import SliderThumb, slider

_EPOCH = date(1970, 1, 1)
_BUFFER = timedelta(days=31)


@dataclass(frozen=True)
class TimelineCategory:
    """A category of timeline events: one chip and one look of markers.

    Attributes
    ----------
    key : str
        Referenced by the events and written into the URL.
    label : str
        The chip's text (a plural, e.g. ``"Releases"``).
    color : str
        A CSS colour of its dots, icons and bars.
    icon : IconName
        The icon of its markers.
    shown : bool
        Whether it is shown by default (the chips' "Default").
    """

    key: str
    label: str
    color: str
    icon: IconName
    shown: bool = True


@dataclass(frozen=True)
class TimelineEvent:
    """One event on the axis.

    Attributes
    ----------
    key : str
        Sent to ``open_url`` when its marker is opened; unique.
    category : str
        The key of its :class:`TimelineCategory`.
    start : date
        Where it sits on the axis.
    label : str
        Accessible name of a marker with only this event (say what and when).
    end : date | None
        The end of a period; it then also shows as a bar.
    warn : bool
        Draw its marker in the warning colour.
    """

    key: str
    category: str
    start: date
    label: str
    end: date | None = None
    warn: bool = False


@dataclass(frozen=True)
class TimelineQuery:
    """Names of the URL parameters the timeline keeps its state in."""

    categories: str = "categories"
    start: str = "from"
    end: str = "to"


def _day(value: date) -> int:
    """Days since 1970-01-01: the slider's scale and the script's unit."""
    return (value - _EPOCH).days


def _months(start: date, end: date) -> list[tuple[date, date]]:
    """The calendar months from ``start``'s to ``end``'s, each as [first day, first day of the next)."""
    out = []
    first = start.replace(day=1)
    while first <= end:
        nxt = (first + timedelta(days=32)).replace(day=1)
        out.append((first, nxt))
        first = nxt
    return out


class _Timeline:
    """Public entry point for the timeline primitive (the :data:`timeline` singleton)."""

    def __call__(
        self,
        events: Sequence[TimelineEvent],
        categories: Sequence[TimelineCategory],
        *,
        open_url: str,
        shown: Sequence[str] | None = None,
        span: tuple[date, date] | None = None,
        bounds: tuple[date, date] | None = None,
        query: TimelineQuery | None = None,
        id: str = "timeline",
        **kwargs: y.Attribute,
    ) -> y.Node:
        """Render the timeline.

        Args:
            events: The events, in any order.
            categories: The categories, in the order of their chips.
            open_url: Requested with the keys of a marker's events (repeated
                ``key`` parameter) into the drawer.
            shown: The categories shown at first; unknown keys are ignored.
                ``None``: those with ``shown=True``.
            span: The span shown at first, clamped to ``bounds``; ``None`` or
                an empty span: the bounds.
            bounds: The slider's ends. ``None``: from a month before the
                earliest to a month after the latest date of the events
                (around today without events).
            query: Keep the shown categories and span in the page's URL under
                these names.
            id: DOM id of the timeline; the slider's inputs are named
                ``{id}-span``.
            **kwargs: Extra HTML attributes forwarded to the outer ``<div>``.

        Raises:
            ValueError: If keys of categories or events repeat, an event's
                category is unknown, an event ends before it starts, or the
                bounds are empty.
        """
        keys = [c.key for c in categories]
        if len(set(keys)) != len(keys):
            raise ValueError("timeline category keys must be unique")
        if len({e.key for e in events}) != len(events):
            raise ValueError("timeline event keys must be unique")
        for e in events:
            if e.category not in keys:
                raise ValueError(
                    f"timeline event {e.key!r} has an unknown category {e.category!r}"
                )
            if e.end is not None and e.end < e.start:
                raise ValueError(f"timeline event {e.key!r} ends before it starts")

        if bounds is None:
            if events:
                first = min(e.start for e in events)
                last = max(e.end or e.start for e in events)
            else:
                first = last = datetime.now(UTC).date()
            bounds = (first - _BUFFER, last + _BUFFER)
        lo, hi = bounds
        if not lo < hi:
            raise ValueError(f"timeline bounds are empty: {lo} – {hi}")
        start, end = span or bounds
        start, end = max(lo, start), min(hi, end)
        if not start < end:
            start, end = lo, hi

        visible = (
            {c.key for c in categories if c.shown}
            if shown is None
            else set(shown) & set(keys)
        )

        def in_span(e: TimelineEvent) -> bool:
            return (e.end or e.start) >= start and e.start <= end

        counts = {
            k: sum(1 for e in events if e.category == k and in_span(e)) for k in keys
        }
        months = _months(lo, hi)
        per_month = [
            sum(1 for e in events if e.category in visible and a <= e.start < b)
            for a, b in months
        ]
        most = max(per_month, default=0) or 1

        data = [
            {
                "key": e.key,
                "category": e.category,
                "start": e.start.isoformat(),
                "end": e.end.isoformat() if e.end else None,
                "label": e.label,
                "warn": e.warn,
            }
            for e in sorted(events, key=lambda e: (e.start, e.key))
        ]

        return y.div(
            **classnames(
                "hx-timeline",
                id=id,
                data_timeline=True,
                data_timeline_open_url=open_url,
                data_timeline_query=json.dumps(asdict(query)) if query else None,
                data_timeline_default=",".join(c.key for c in categories if c.shown),
                # Translators: the line above a timeline; all three are numbers.
                data_text_summary=_("{shown} of {total} events in {markers} markers"),
                # Translators: accessible name of a timeline marker that combines events; {dates} is a date or a range.
                data_text_group=_("{n} events, {dates}"),
                # Translators: added to the accessible name of a timeline marker with a flagged event.
                data_text_warn=_("with a warning"),
                data_text_empty=_("No events of these categories in this period."),
                **kwargs,
            )
        )[
            y.div(
                class_="hx-timeline__filters",
                role="group",
                aria_label=_("Categories"),
            )[
                (
                    y.button(
                        **classnames(
                            "hx-timeline__chip",
                            type="button",
                            aria_pressed="true" if c.key in visible else "false",
                            data_timeline_category=c.key,
                            **merge_styles({"--timeline--color": c.color}),
                        )
                    )[
                        y.span(class_="hx-timeline__chip-dot", aria_hidden="true"),
                        y.span[c.label],
                        y.span(class_="hx-timeline__chip-count")[str(counts[c.key])],
                    ]
                    for c in categories
                ),
                y.span(class_="hx-timeline__presets")[
                    # Translators: brings back the categories a timeline shows by default.
                    button(
                        _("Default"),
                        variant="ghost",
                        size="sm",
                        type="button",
                        data_timeline_action="default",
                    ),
                    button(
                        _("All"),
                        variant="ghost",
                        size="sm",
                        type="button",
                        data_timeline_action="all",
                    ),
                ],
            ],
            y.p(class_="hx-timeline__summary", aria_live="polite"),
            y.div(class_="hx-timeline__axis", data_timeline_axis=True),
            y.div(class_="hx-timeline__range")[
                y.div(class_="hx-timeline__range-head")[
                    y.span[_("Period"), " ", y.strong(data_timeline_span_label=True)],
                    button(
                        _("Whole period"),
                        variant="outline",
                        size="sm",
                        type="button",
                        data_timeline_action="reset",
                    ),
                ],
                y.div(class_="hx-timeline__range-control")[
                    y.div(class_="hx-timeline__strip", aria_hidden="true")[
                        (
                            y.span(
                                **classnames(
                                    "hx-timeline__strip-bar",
                                    data_timeline_month=f"{_day(a)},{_day(b)}",
                                    **merge_styles(
                                        {
                                            "--timeline--height": f"{round(100 * n / most)}%"
                                        }
                                    ),
                                )
                            )
                            for (a, b), n in zip(months, per_month, strict=True)
                        )
                    ],
                    slider(
                        f"{id}-span",
                        (
                            SliderThumb(_day(start), label=_("Start")),
                            SliderThumb(_day(end), label=_("End")),
                        ),
                        min=_day(lo),
                        max=_day(hi),
                        step=1,
                    ),
                ],
                y.div(class_="hx-timeline__range-ends", aria_hidden="true")[
                    y.span(data_timeline_bound=str(_day(lo))),
                    y.span(data_timeline_bound=str(_day(hi))),
                ],
            ],
            y.script(type="application/json", data_timeline_events=True)[
                # `</` can't end the script element early: escaped as JSON allows.
                Markup(json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
            ],
            (y.template(data_timeline_icon=c.key)[icon(c.icon)] for c in categories),
        ]


timeline = _Timeline()
