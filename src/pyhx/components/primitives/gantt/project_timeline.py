"""The project-timeline gantt: ``gantt.project_timeline(...)``.

One group per :class:`ProjectTimeline`: a group-header row carrying just the
project title (empty day cells) followed by the shared indented activity rows —
the same col-spanning timespan bars as the planned-utilization chart.
"""

from datetime import date

import htpy as y

from ...view_model import CalendarLabels
from ..table import table
from ._shared import _activity_row, _gantt_shell
from .model import HilightedDate, ProjectTimeline


class _ProjectTimelineGantt:
    """Render a project-timeline Gantt as a ``hx-table``.

    Reached via the factory as ``gantt.project_timeline(...)``. Renders the
    timeline header, then one group of body rows per :class:`ProjectTimeline`:

    * a group-header row — the project ``title`` in the leading column, with
      empty day cells across the timeline;
    * one indented row per :class:`PlannedActivity` — the activity label, then a
      col-spanning :data:`bubble` bar for each timespan (identical to the
      planned-utilization chart's activity rows).

    The timeline is wider than its container, so the table is wrapped in a
    ``table.scroll_container`` for horizontal scrolling.
    """

    def __call__(
        self,
        start_date: date,
        end_date: date,
        item_header_label: y.Node = "",
        timelines: list[ProjectTimeline] | None = None,
        highlighted_dates: list[HilightedDate] | None = None,
        calendar_labels: CalendarLabels = CalendarLabels(),
    ) -> y.Node:
        """Render the Gantt.

        Args:
            start_date: First day of the timeline (inclusive).
            end_date: Last day of the timeline (inclusive).
            item_header_label: Header content for the leading label column, to
                the left of the timeline.
            timelines: Project groups rendered as body rows. ``None`` renders the
                timeline header alone.
            highlighted_dates: Days to emphasise in the header.
            calendar_labels: Weekday/month label vocabulary (localisation hook).
        """
        return _gantt_shell(
            start_date,
            end_date,
            item_header_label,
            lambda days: [
                row
                for timeline in timelines or []
                for row in self._project_rows(timeline, days)
            ],
            highlighted_dates=highlighted_dates,
            calendar_labels=calendar_labels,
        )

    def _project_rows(
        self, timeline: ProjectTimeline, days: list[date]
    ) -> list[y.Node]:
        """A group-header row (title + empty day cells), then one row per activity."""
        rows: list[y.Node] = [
            table.tr(level=1)[
                table.th[timeline.title],
                *(table.td[""] for _ in days),
            ]
        ]
        rows += [_activity_row(activity, days) for activity in timeline.activities]
        return rows
