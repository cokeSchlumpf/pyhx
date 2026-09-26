"""Gantt demo page — blank scaffold for the ``gantt`` skeleton component.

Reserves the route and the sample-app wiring for the Gantt chart. The
component is a skeleton for now, so this page just renders the empty
container; add live demos here as the component grows.
"""

# docs:start imports
from datetime import date

import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


# docs:start entries_data
# Two team members. A. Okafor is over-allocated on Aug 6 (130%), so her row
# shows the 100% reference rule (solid where over, muted elsewhere). B. Silva
# never exceeds 100% — his row shows no rule at all, and his exactly-100% day
# simply fills the cell. Colours are optional — a `None` colour falls back to a
# primary shade.
PLANNED_UTILIZATION = c.PlannedUtilization(
    label="A. Okafor",
    planned={
        date(2026, 8, 3): [
            c.PlannedUtilizationItem("Project Alpha", c.Color.info(), c.Pct.of(60)),
            c.PlannedUtilizationItem("Support", c.Color.warning(), c.Pct.of(25)),
        ],
        date(2026, 8, 4): [
            c.PlannedUtilizationItem("Project Alpha", c.Color.info(), c.Pct.of(80)),
        ],
        date(2026, 8, 5): [
            c.PlannedUtilizationItem("Project Alpha", c.Color.info(), c.Pct.of(60)),
            c.PlannedUtilizationItem("Support", c.Color.warning(), c.Pct.of(50)),
        ],
        # Over-allocated (130%) — the busiest day, so it sets the row scale and
        # shows the 100% danger rule with the overflow rising above it.
        date(2026, 8, 6): [
            c.PlannedUtilizationItem("Project Alpha", c.Color.info(), c.Pct.of(90)),
            c.PlannedUtilizationItem("Support", c.Color.warning(), c.Pct.of(40)),
        ],
        date(2026, 8, 7): [
            c.PlannedUtilizationItem("Project Alpha", c.Color.info(), c.Pct.of(40)),
        ],
    },
    activities=[
        c.PlannedActivity(
            label="Project Alpha",
            timespans=[
                c.PlannedTimespan(
                    label="Design",
                    title="Design phase",
                    color=c.Color.info(),
                    start=date(2026, 8, 3),
                    end=date(2026, 8, 7),
                ),
                c.PlannedTimespan(
                    label="Build",
                    title="Build phase",
                    color=c.Color.success(),
                    start=date(2026, 8, 10),
                    end=date(2026, 8, 18),
                ),
            ],
        ),
        c.PlannedActivity(
            label="Support rota",
            timespans=[
                # No colour — falls back to a primary shade.
                c.PlannedTimespan(
                    label="On call",
                    title="On-call week",
                    color=None,
                    start=date(2026, 8, 12),
                    end=date(2026, 8, 16),
                ),
            ],
        ),
    ],
)

# A second member with no over-allocation: every day is at or below 100%, so his
# row carries no 100% rule. Aug 4 is exactly 100% and simply fills the cell.
PLANNED_UTILIZATION_CLEAR = c.PlannedUtilization(
    label="B. Silva",
    planned={
        date(2026, 8, 3): [
            c.PlannedUtilizationItem("Project Beta", c.Color.success(), c.Pct.of(50)),
        ],
        date(2026, 8, 4): [
            c.PlannedUtilizationItem("Project Beta", c.Color.success(), c.Pct.of(70)),
            c.PlannedUtilizationItem("Support", c.Color.warning(), c.Pct.of(30)),
        ],
        date(2026, 8, 5): [
            c.PlannedUtilizationItem("Project Beta", c.Color.success(), c.Pct.of(60)),
        ],
        date(2026, 8, 6): [
            c.PlannedUtilizationItem("Project Beta", c.Color.success(), c.Pct.of(80)),
        ],
        date(2026, 8, 7): [
            c.PlannedUtilizationItem("Project Beta", c.Color.success(), c.Pct.of(45)),
        ],
    },
    activities=[
        c.PlannedActivity(
            label="Project Beta",
            timespans=[
                c.PlannedTimespan(
                    label="Spec",
                    title="Spec phase",
                    color=c.Color.success(),
                    start=date(2026, 8, 3),
                    end=date(2026, 8, 9),
                ),
                c.PlannedTimespan(
                    label="Rollout",
                    title="Rollout",
                    color=c.Color.info(),
                    start=date(2026, 8, 12),
                    end=date(2026, 8, 19),
                ),
            ],
        ),
    ],
)
# docs:end entries_data


# docs:start project_timelines_data
# Two projects. Each renders a title row (empty day cells) followed by its
# activities as col-spanning timespan bars — the same bars as the utilization
# chart, minus the daily-load row. A `None` timespan colour falls back to a
# primary shade.
PROJECT_ALPHA = c.ProjectTimeline(
    title="Project Alpha",
    activities=[
        c.PlannedActivity(
            label="Discovery",
            timespans=[
                c.PlannedTimespan(
                    label="Research",
                    title="Research",
                    color=c.Color.info(),
                    start=date(2026, 8, 3),
                    end=date(2026, 8, 7),
                ),
                c.PlannedTimespan(
                    label="Spec",
                    title="Spec",
                    color=c.Color.success(),
                    start=date(2026, 8, 10),
                    end=date(2026, 8, 14),
                ),
            ],
        ),
        c.PlannedActivity(
            label="Delivery",
            timespans=[
                c.PlannedTimespan(
                    label="Build",
                    title="Build phase",
                    color=None,
                    start=date(2026, 8, 12),
                    end=date(2026, 8, 20),
                ),
            ],
        ),
    ],
)
PROJECT_BETA = c.ProjectTimeline(
    title="Project Beta",
    activities=[
        c.PlannedActivity(
            label="Rollout",
            timespans=[
                c.PlannedTimespan(
                    label="Pilot",
                    title="Pilot",
                    color=c.Color.warning(),
                    start=date(2026, 8, 5),
                    end=date(2026, 8, 11),
                ),
                c.PlannedTimespan(
                    label="GA",
                    title="General availability",
                    color=c.Color.info(),
                    start=date(2026, 8, 14),
                    end=date(2026, 8, 21),
                ),
            ],
        ),
    ],
)
# docs:end project_timelines_data


router = WebAppRouter()


@router.page("/gantt", title="Gantt")
async def gantt_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Gantt"],
            y.p[
                "The ",
                y.code["c.gantt"],
                " primitive is a skeleton scaffold for the Gantt-chart "
                "component. It renders an empty ",
                y.code["<div class=\"hx-gantt\">"],
                " container today — no timeline, bars or axis yet. This page "
                "reserves the route; add demos here as the component grows.",
            ],
            # --- Planned utilization: timeline header ----------------------
            y.h2["Planned utilization"],
            y.p[
                "Call ",
                y.code["c.gantt.planned_utilization"],
                " with a start and end date to render the timeline header — a ",
                "month / weekday / date ",
                y.code["thead"],
                " spanning the range (inclusive), with a leading label column. ",
                "Weekend columns are shaded, and the table wraps in a scroll ",
                "container so a long timeline scrolls horizontally. Only the ",
                "header renders for now — the utilization rows are still to come.",
            ],
            # docs:start planned_utilization
            c.gantt.planned_utilization(
                date(2026, 3, 1),
                date(2026, 4, 15),
                item_header_label="Team member",
            ),
            # docs:end planned_utilization
            c.code([("code", src.text("planned_utilization"), "python")]),
            # --- Partial months: ellipsis + tooltip ------------------------
            y.h2["Partial months"],
            y.p[
                "When the timeline starts or ends mid-month, a month cell can be "
                "narrower than its label — here it opens on the last two days of "
                "March. The label clips with an ellipsis, and the full ",
                y.code["Month Year"],
                " stays available as a hover tooltip.",
            ],
            # docs:start partial_months
            c.gantt.planned_utilization(
                date(2026, 3, 30),
                date(2026, 4, 10),
                item_header_label="Team member",
            ),
            # docs:end partial_months
            c.code([("code", src.text("partial_months"), "python")]),
            # --- Highlighted dates -----------------------------------------
            y.h2["Highlighted dates"],
            y.p[
                "Pass ",
                y.code["highlighted_dates"],
                " to emphasise specific days. Each ",
                y.code["c.HilightedDate"],
                " tints its weekday and date cells with the given ",
                y.code["appearance"],
                " and carries its ",
                y.code["title"],
                " as a hover tooltip. A highlight wins over the weekend wash, so "
                "Swiss National Day (Aug 1, a Saturday) reads as a holiday rather "
                "than a plain weekend.",
            ],
            # docs:start highlighted_dates
            c.gantt.planned_utilization(
                date(2026, 8, 1),
                date(2026, 8, 21),
                item_header_label="Team member",
                highlighted_dates=[
                    c.HilightedDate(
                        title="Swiss National Day",
                        date=date(2026, 8, 1),
                        appearance="danger",
                    ),
                    c.HilightedDate(
                        title="Company Event",
                        date=date(2026, 8, 13),
                        appearance="primary",
                    ),
                    c.HilightedDate(
                        title="Sprint review",
                        date=date(2026, 8, 20),
                        appearance="info",
                    ),
                ],
            ),
            # docs:end highlighted_dates
            c.code([("code", src.text("highlighted_dates"), "python")]),
            # --- Planned load & activities ---------------------------------
            y.h2["Planned load & activities"],
            y.p[
                "Pass ",
                y.code["entries"],
                " — a list of ",
                y.code["c.PlannedUtilization"],
                " — to fill the body. Each entry adds a planned-load row (the ",
                "daily ",
                y.code["planned"],
                " items rendered as a stacked bar per day) followed by one "
                "indented row per activity, whose non-overlapping timespans are "
                "drawn as col-spanning bubble bars. Timespans without a colour "
                "fall back to a primary shade.",
            ],
            # docs:start entries
            c.gantt.planned_utilization(
                date(2026, 8, 3),
                date(2026, 8, 21),
                item_header_label="Team member",
                entries=[PLANNED_UTILIZATION, PLANNED_UTILIZATION_CLEAR],
                highlighted_dates=[
                    c.HilightedDate(
                        title="Milestone",
                        date=date(2026, 8, 12),
                        appearance="primary",
                    ),
                    c.HilightedDate(
                        title="Release",
                        date=date(2026, 8, 19),
                        appearance="danger",
                    ),
                ],
            ),
            # docs:end entries
            c.code(
                [
                    ("code", src.text("entries"), "python"),
                    ("data", src.text("entries_data"), "python"),
                ]
            ),
            # --- Project timeline ------------------------------------------
            y.h2["Project timeline"],
            y.p[
                "Call ",
                y.code["c.gantt.project_timeline"],
                " with a list of ",
                y.code["c.ProjectTimeline"],
                ". Each project adds a title row (with empty day cells) followed "
                "by one indented row per activity — the same col-spanning bubble "
                "bars as the utilization chart, without the daily-load row.",
            ],
            # docs:start project_timeline
            c.gantt.project_timeline(
                date(2026, 8, 3),
                date(2026, 8, 21),
                item_header_label="Project",
                timelines=[PROJECT_ALPHA, PROJECT_BETA],
            ),
            # docs:end project_timeline
            c.code(
                [
                    ("code", src.text("project_timeline"), "python"),
                    ("data", src.text("project_timelines_data"), "python"),
                ]
            ),
        ]
    )
