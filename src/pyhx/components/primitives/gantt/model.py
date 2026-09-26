"""Value types for the gantt charts — the data a chart builder consumes.

Pure data classes (no rendering): the planned-utilization model
(:class:`PlannedUtilization` and its items), the project-timeline model
(:class:`ProjectTimeline`), the shared :class:`PlannedActivity` /
:class:`PlannedTimespan`, and the header's :class:`HilightedDate`.
"""

import itertools
from dataclasses import dataclass
from datetime import date

import htpy as y

from ...variants import Appearance
from ...view_model import Color, Pct


@dataclass(frozen=True)
class PlannedUtilizationItem:
    title: str
    color: Color | None
    percent: Pct


@dataclass(frozen=True)
class PlannedTimespan:
    label: y.Node
    title: str
    color: Color | None

    start: date
    end: date

    #: Bubble text colour. Defaults to ``neutral-050`` — near-white, so it reads
    #: against the (primary-family) bar fill.
    text_color: Color = Color.neutral(50)

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(
                f"timespan ends before it starts: {self.start} > {self.end}"
            )


@dataclass(frozen=True)
class PlannedActivity:
    label: y.Node
    timespans: list[PlannedTimespan]

    def __post_init__(self) -> None:
        # Timespans within an activity may not overlap: ordered by start, each
        # must begin strictly after the previous one ends.
        ordered = sorted(self.timespans, key=lambda span: span.start)
        for earlier, later in itertools.pairwise(ordered):
            if later.start <= earlier.end:
                raise ValueError(
                    "overlapping timespans in activity: "
                    f"{earlier.start}–{earlier.end} overlaps "
                    f"{later.start}–{later.end}"
                )


@dataclass
class PlannedUtilization:
    label: y.Node
    planned: dict[date, list[PlannedUtilizationItem]]
    activities: list[PlannedActivity]


@dataclass(frozen=True)
class HilightedDate:
    title: str
    date: date
    appearance: Appearance


@dataclass(frozen=True)
class ProjectTimeline:
    title: str
    activities: list[PlannedActivity]
