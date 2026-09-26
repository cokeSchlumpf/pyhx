"""The timeline table header — a month / weekday / date ``thead``.

:class:`TimelineTableHeader` renders the three stacked header rows shared by
every gantt chart. The module-level :data:`_timeline_header` singleton is the
stateless renderer the chart builders call.
"""

from datetime import date
from itertools import groupby

import htpy as y
from commons import datetime_operators

from ...view_model import CalendarLabels
from ..table import table
from .model import HilightedDate


class TimelineTableHeader:
    def __call__(
        self,
        start_date: date,
        end_date: date,
        columns_before: tuple[y.Node, y.Node, y.Node] | None = None,
        highlighted_dates: list[HilightedDate] | None = None,
        calendar_labels: CalendarLabels = CalendarLabels(),
    ) -> y.Node:
        """Render a ``table.thead`` with three rows spanning ``start_date`` to
        ``end_date`` (inclusive): month, weekday and zero-padded day number.

        The month row carries one cell per month, spanning that month's days. The
        first month — and every subsequent year change — appends the year (e.g.
        ``"March 2026"``, then ``"April"``, ``"July"``, then ``"January 2027"``).
        Weekday and date cells for Saturday/Sunday carry a ``hx-gantt__weekend``
        class for shading.

        Args:
            start_date: First day of the timeline (inclusive).
            end_date: Last day of the timeline (inclusive).
            columns_before: Leading header cell content for each of the three
                rows — one node per row — placed to the left of the timeline to
                align with a label column. ``None`` renders no leading column.
            highlighted_dates: Days to emphasise; each adds a
                ``hx-gantt__highlight--{appearance}`` class (and the item's
                ``title`` as a tooltip) to that day's weekday and date cells. If
                two items share a date, the last one wins.
            calendar_labels: Weekday/month label vocabulary (localisation hook).
        """
        days = list(datetime_operators.date_range(start_date, end_date))
        highlights = {h.date: h for h in highlighted_dates or []}

        # Month row: one cell per month, spanning that month's days. The visible
        # label appends the year only on the first month and each year change,
        # but the title always carries the full "Month Year" — so a cell whose
        # label is clipped to an ellipsis still reveals the full month on hover.
        month_cells: list[y.Node] = []
        shown_year: int | None = None
        for (year, _month), month_days in groupby(
            days, key=lambda d: (d.year, d.month)
        ):
            days_in_month = list(month_days)
            first = days_in_month[0]
            span = len(days_in_month)
            month_name = calendar_labels.month(first)
            title = f"{month_name} {year}"
            label = title if year != shown_year else month_name
            shown_year = year
            month_cells.append(
                table.th(class_="hx-gantt__month", span=span, title=title)[label]
            )

        # Weekday initial and zero-padded day number — one cell per day. Weekend
        # days carry a modifier class; highlighted days carry an appearance class
        # and the item's title as a tooltip.
        def _day_cell(content: y.Node, day: date) -> y.Node:
            classes = ["hx-gantt__weekend"] if day.weekday() >= 5 else []
            highlight = highlights.get(day)
            if highlight is not None:
                classes.append(f"hx-gantt__highlight--{highlight.appearance}")
            if not classes:
                return table.th[content]
            # `title=None` is omitted by htpy, so a weekend-only cell renders no
            # tooltip; a highlighted cell carries the item's title.
            title = highlight.title if highlight is not None else None
            return table.th(class_=" ".join(classes), title=title)[content]

        weekday_cells = [_day_cell(calendar_labels.weekday(d), d) for d in days]
        date_cells = [_day_cell(f"{d.day:02d}", d) for d in days]

        # Optional leading cell per row, keeping the grid aligned with a label
        # column to the left of the timeline.
        before = columns_before or (None, None, None)
        return table.thead[
            table.tr[table.th[before[0]] if columns_before else None, month_cells],
            table.tr[table.th[before[1]] if columns_before else None, weekday_cells],
            table.tr[table.th[before[2]] if columns_before else None, date_cells],
        ]


#: Shared, stateless timeline-header renderer used by the gantt builders.
_timeline_header = TimelineTableHeader()
