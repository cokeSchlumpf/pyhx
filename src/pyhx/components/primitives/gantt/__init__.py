"""The ``gantt`` primitive: timeline charts rendered as a ``hx-table``.

The public entry point is the :data:`gantt` factory. Its sub-builders render the
two chart types:

* ``gantt.planned_utilization(...)`` — stacked daily load + activity bars.
* ``gantt.project_timeline(...)`` — a title row per project + activity bars.

The chart data types (``PlannedUtilization``, ``ProjectTimeline``, and the
shared ``PlannedActivity`` / ``PlannedTimespan`` …) are re-exported here.
"""

from .factory import gantt
from .model import (
    HilightedDate,
    PlannedActivity,
    PlannedTimespan,
    PlannedUtilization,
    PlannedUtilizationItem,
    ProjectTimeline,
)

__all__ = [
    "HilightedDate",
    "PlannedActivity",
    "PlannedTimespan",
    "PlannedUtilization",
    "PlannedUtilizationItem",
    "ProjectTimeline",
    "gantt",
]
