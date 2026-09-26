"""The planned-utilization gantt: ``gantt.planned_utilization(...)``.

One group per :class:`PlannedUtilization`: a group-header row of stacked daily
load (with a 100% over-allocation reference rule) followed by the shared
indented activity rows.
"""

from datetime import date

import htpy as y

from ...view_model import CalendarLabels, Pct
from ..table import StackChartItem, table
from ._shared import _activity_row, _fallback_color, _gantt_shell
from .model import HilightedDate, PlannedUtilization, PlannedUtilizationItem

#: Tolerance for the 100% over-allocation test, so a day that is meant to be
#: exactly 100% isn't tipped "over" by floating-point rounding of its percents.
_OVER_ALLOCATION_EPSILON = 1e-9


class _PlannedUtilizationGantt:
    """Render a planned-utilization Gantt as a ``hx-table``.

    Reached via the factory as ``gantt.planned_utilization(...)``. Renders the
    month/weekday/date timeline header, then one group of body rows per
    :class:`PlannedUtilization` entry:

    * a *planned-load* row — the entry label, then a stacked-bar cell per day
      summing that day's :class:`PlannedUtilizationItem` s (empty where nothing
      is planned);
    * one indented row per :class:`PlannedActivity` — the activity label, then a
      col-spanning :data:`bubble` bar for each timespan and empty cells in the
      gaps between them.

    The timeline is wider than its container, so the table is wrapped in a
    ``table.scroll_container`` for horizontal scrolling.
    """

    def __call__(
        self,
        start_date: date,
        end_date: date,
        item_header_label: y.Node = "",
        entries: list[PlannedUtilization] | None = None,
        highlighted_dates: list[HilightedDate] | None = None,
        calendar_labels: CalendarLabels = CalendarLabels(),
    ) -> y.Node:
        """Render the Gantt.

        Args:
            start_date: First day of the timeline (inclusive).
            end_date: Last day of the timeline (inclusive).
            item_header_label: Header content for the leading label column, to
                the left of the timeline.
            entries: Planned-utilization groups rendered as body rows. ``None``
                renders the timeline header alone.
            highlighted_dates: Days to emphasise in the header.
            calendar_labels: Weekday/month label vocabulary (localisation hook).
        """
        return _gantt_shell(
            start_date,
            end_date,
            item_header_label,
            lambda days: [
                row for entry in entries or [] for row in self._entry_rows(entry, days)
            ],
            highlighted_dates=highlighted_dates,
            calendar_labels=calendar_labels,
        )

    def _entry_rows(self, entry: PlannedUtilization, days: list[date]) -> list[y.Node]:
        """A planned-load row for the entry, then one indented row per activity."""
        rows: list[y.Node] = [
            table.tr(level=1)[
                table.th[entry.label],
                *self._planned_cells(entry.planned, days),
            ]
        ]
        rows += [_activity_row(activity, days) for activity in entry.activities]
        return rows

    @staticmethod
    def _planned_cells(
        planned: dict[date, list[PlannedUtilizationItem]], days: list[date]
    ) -> list[y.Node]:
        """One cell per day: a stacked-bar chart of that day's planned items, or
        an empty cell when nothing is planned.

        The whole row shares one vertical scale — the busiest day's total load,
        but never below 100% — so bar heights compare across days and an
        over-allocated day fills the cell. Days over 100% carry a danger rule at
        the 100% mark, above which the over-allocation rises.
        """
        totals = {
            day: sum(item.percent.value for item in items)
            for day, items in planned.items()
        }
        scale = max([1.0, *totals.values()])
        # Once any day is *over* budget (strictly above 100%) the rule becomes a
        # row-wide reference: solid danger on the over-allocated days, muted on
        # the rest (empty days too). A day at exactly 100% stays muted.
        over_limit = 1.0 + _OVER_ALLOCATION_EPSILON
        show_reference = scale > over_limit
        limit_bottom = f"bottom: {100 / scale:.4g}%"

        def _limit(day: date) -> y.Node | None:
            if not show_reference:
                return None
            classes = ["hx-gantt__load-limit"]
            if totals.get(day, 0.0) <= over_limit:
                classes.append("hx-gantt__load-limit--muted")
            return y.div(class_=" ".join(classes), style=limit_bottom)

        cells: list[y.Node] = []
        for day in days:
            items = planned.get(day)
            overlay = _limit(day)
            if not items:
                # An empty day still carries the reference line (as an empty
                # stack) so the 100% axis runs the full row.
                cells.append(
                    table.stack_chart_cell([], overlay=overlay)
                    if overlay is not None
                    else table.td[""]
                )
                continue
            cells.append(
                table.stack_chart_cell(
                    [
                        StackChartItem(
                            # Tooltip shows the item's own planned share, not its
                            # height on the row's (normalised) scale.
                            color=item.color or _fallback_color(i),
                            title=f"{item.title} — {round(item.percent.percent)}%",
                            percent=Pct(item.percent.value / scale),
                        )
                        for i, item in enumerate(items)
                    ],
                    overlay=overlay,
                )
            )
        return cells
