"""The gantt factory (the :data:`gantt` singleton) and its sub-builders."""

from .planned_utilization import _PlannedUtilizationGantt
from .project_timeline import _ProjectTimelineGantt


class _KxGanttFactory:
    """Public entry point for the gantt primitive (the :data:`gantt` singleton).

    Call or subscript it to build a chart:

    * ``gantt()[content]`` — configure, then fill.
    * ``gantt[content]`` — a default chart, filled directly.

    Sub-builders are exposed as attributes:

    * ``gantt.planned_utilization(...)`` — a planned-utilization Gantt.
    * ``gantt.project_timeline(...)`` — a project-timeline Gantt.
    """

    def __init__(self) -> None:
        self.planned_utilization = _PlannedUtilizationGantt()
        self.project_timeline = _ProjectTimelineGantt()


#: The gantt primitive. Import as ``from pyhx.components import gantt`` (or via
#: ``c.gantt``) and use ``gantt(...)`` / ``gantt[...]`` plus its sub-builders.
gantt = _KxGanttFactory()
