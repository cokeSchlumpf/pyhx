"""Machinery shared by the gantt chart builders.

The chart shell (:func:`_gantt_shell`), the indented activity row
(:func:`_activity_row`) and its cells (:func:`_activity_cells`), the timespan
bubble (:func:`_timespan_bubble`) and the fallback colour ramp
(:func:`_fallback_color`) are identical across chart types; each builder differs
only in the group-header row it contributes to the body.
"""

from collections.abc import Callable
from datetime import date

import htpy as y
from commons import datetime_operators

from ....core.primitives import classnames as cx
from ...view_model import CalendarLabels, Color
from ..bubble import bubble
from ..table import table
from .header import _timeline_header
from .model import HilightedDate, PlannedActivity, PlannedTimespan

#: Default width of the leading label column. Fixed (not auto-fit) so the grid is
#: deterministic; a resize handle in its header cell lets the user widen it.
_LABEL_COLUMN_WIDTH = "300px"

#: Width of each day track. Fixed, so a long timeline overflows and scrolls
#: rather than squeezing days to illegible slivers.
_DAY_COLUMN_WIDTH = "44px"

#: Left padding on an activity's label cell, nesting it one step under its group
#: row. Set explicitly rather than relying on the table's ``aria-level`` indent —
#: that indent's first step equals the base cell padding, so a level-2 row would
#: not read as indented.
_ACTIVITY_LABEL_INDENT = "calc(2 * var(--hx-spacing-md))"


def _fallback_color(index: int) -> Color:
    """A primary-family tint for the ``index``-th otherwise-uncoloured segment.

    ``primary`` exposes no numeric palette shades, so derive distinguishable
    ones by mixing it toward the page background — each successive segment reads
    as a lighter primary.
    """
    mix = max(100 - index * 25, 25)
    return Color.css(
        f"color-mix(in srgb, var(--hx-color-primary) {mix}%, var(--hx-color-background))"
    )


def _timespan_bubble(span: PlannedTimespan, order: int) -> y.Node:
    """A bubble bar for one timespan; falls back to a primary shade when the
    timespan carries no colour of its own."""
    color = span.color or _fallback_color(order)
    return bubble(
        color=str(color),
        text_color=str(span.text_color),
        size="sm",
        title=span.title,
    )[span.label]


def _activity_cells(activity: PlannedActivity, days: list[date]) -> list[y.Node]:
    """Walk the timeline left to right: a col-spanning bubble bar for each
    timespan (clamped to the visible range), an empty cell everywhere else."""
    first, last = days[0], days[-1]
    column_of = {day: i for i, day in enumerate(days)}

    # Clamp each timespan to the visible window, dropping any that fall wholly
    # outside it; key the survivors by their starting column. No two share a
    # column — PlannedActivity forbids overlaps.
    by_start: dict[int, tuple[int, PlannedTimespan, int]] = {}
    for order, span in enumerate(activity.timespans):
        visible_start = max(span.start, first)
        visible_end = min(span.end, last)
        if visible_start > visible_end:
            continue
        by_start[column_of[visible_start]] = (column_of[visible_end], span, order)

    cells: list[y.Node] = []
    col = 0
    while col < len(days):
        match = by_start.get(col)
        if match is None:
            cells.append(table.td[""])
            col += 1
            continue
        end_col, span, order = match
        cells.append(
            table.td(kind="layout", span=end_col - col + 1)[
                _timespan_bubble(span, order)
            ]
        )
        col = end_col + 1
    return cells


def _activity_row(activity: PlannedActivity, days: list[date]) -> y.Node:
    """One indented (level-2) activity row: the label, then its timespan bars."""
    return table.tr(level=2)[
        table.th(style=f"padding-left: {_ACTIVITY_LABEL_INDENT}")[activity.label],
        *_activity_cells(activity, days),
    ]


def _gantt_shell(
    start_date: date,
    end_date: date,
    item_header_label: y.Node,
    build_body: Callable[[list[date]], list[y.Node]],
    highlighted_dates: list[HilightedDate] | None = None,
    calendar_labels: CalendarLabels = CalendarLabels(),
) -> y.Node:
    """The common gantt chart frame: a ``hx-gantt`` wrapper around a scrolling
    ``hx-table`` whose ``thead`` is the timeline header and whose ``tbody`` is
    the rows a builder supplies.

    ``days`` is computed once and handed to ``build_body`` so each chart type can
    build its rows against the same timeline without recomputing it.

    Args:
        start_date: First day of the timeline (inclusive).
        end_date: Last day of the timeline (inclusive).
        item_header_label: Header content for the leading label column.
        build_body: Called with the timeline's ``days`` to produce the body rows.
        highlighted_dates: Days to emphasise in the header.
        calendar_labels: Weekday/month label vocabulary (localisation hook).
    """
    # A fixed, resizable label track, then one fixed track per day; the timeline
    # overflows its container and scrolls horizontally.
    days = list(datetime_operators.date_range(start_date, end_date))
    column_widths = f"{_LABEL_COLUMN_WIDTH} repeat({len(days)}, {_DAY_COLUMN_WIDTH})"

    # The corner cell carries the label plus a drag handle that resizes the first
    # (label) track — column index 0 in `--hx-table--cols`.
    label_header = [
        item_header_label,
        table.resize_handle(0, title="Resize label column"),
    ]

    body = build_body(days)

    return y.div(**cx("hx-gantt"))[
        table.scroll_container[
            table(column_widths=column_widths)[
                _timeline_header(
                    start_date,
                    end_date,
                    columns_before=(label_header, "", ""),
                    highlighted_dates=highlighted_dates,
                    calendar_labels=calendar_labels,
                ),
                table.tbody[body] if body else None,
            ]
        ]
    ]
