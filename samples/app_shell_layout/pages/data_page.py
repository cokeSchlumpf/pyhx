"""DataPage demo — a full CRUD page backed by in-memory dummy data.

Shows how a :class:`pyhx.components.DataPage` renders inside the app shell:
a page header (title + create action) above a full-width, scrollable table,
picked up by the app-shell "table-only app page" layout so the table fills the
viewport and scrolls internally. The create/edit/delete actions are real —
they mutate an in-memory ``SimpleDataSource`` list, so no backend is needed.
"""

from datetime import date
from enum import Enum
from typing import Annotated
from uuid import uuid4

import pyhx.components as c
import pyhx.components.data.annotations as a

from pydantic import BaseModel, Field

from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core import WebAppRouter


router = WebAppRouter()


class Status(str, Enum):
    planned = "Planned"
    active = "Active"
    on_hold = "On hold"
    done = "Done"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


@a.form(columns=2)
class Project(BaseModel):
    """One model used for the table, the create form and the edit form alike.

    ``id`` is hidden from the table (``HiddenColumn``) and rendered as a hidden
    form input (``HiddenField``) that round-trips on edit; a fresh ``uuid4`` is
    assigned by ``default_factory`` so every create gets a unique id.
    """

    id: Annotated[str, a.HiddenColumn(), a.HiddenField()] = Field(
        default_factory=lambda: str(uuid4())
    )
    name: Annotated[str, a.TextColumn(label="Name")]
    code: Annotated[str, a.TextColumn(label="Code")]
    status: Annotated[Status, a.TextColumn(label="Status")]
    owner: Annotated[str, a.TextColumn(label="Owner")]
    priority: Annotated[Priority, a.TextColumn(label="Priority")]
    budget: Annotated[
        float,
        a.NumericColumn(
            label="Budget", format=a.CurrencyNumberFormat(currency="EUR")
        ),
    ]
    progress: Annotated[int, a.NumericColumn(label="Progress %")]
    active: Annotated[bool, a.BooleanColumn(label="Active")]
    start_date: Annotated[date, a.DateColumn(label="Start")]
    due_date: Annotated[date, a.DateColumn(label="Due")]


PROJECTS: list[Project] = [
    Project(
        name="Aurora Migration",
        code="AUR-01",
        status=Status.active,
        owner="Anna Schmidt",
        priority=Priority.high,
        budget=185000.0,
        progress=62,
        active=True,
        start_date=date(2024, 1, 15),
        due_date=date(2024, 9, 30),
    ),
    Project(
        name="Billing Revamp",
        code="BILL-02",
        status=Status.planned,
        owner="Marco Rossi",
        priority=Priority.medium,
        budget=92000.0,
        progress=5,
        active=True,
        start_date=date(2024, 6, 1),
        due_date=date(2025, 3, 1),
    ),
    Project(
        name="Customer Portal",
        code="CUST-03",
        status=Status.active,
        owner="Sophie Martin",
        priority=Priority.high,
        budget=240000.0,
        progress=48,
        active=True,
        start_date=date(2023, 11, 6),
        due_date=date(2024, 12, 20),
    ),
    Project(
        name="Data Warehouse",
        code="DWH-04",
        status=Status.on_hold,
        owner="Lena Fischer",
        priority=Priority.medium,
        budget=310000.0,
        progress=30,
        active=False,
        start_date=date(2023, 5, 2),
        due_date=date(2024, 10, 1),
    ),
    Project(
        name="Edge Rollout",
        code="EDGE-05",
        status=Status.done,
        owner="Oliver Novak",
        priority=Priority.low,
        budget=54000.0,
        progress=100,
        active=False,
        start_date=date(2023, 2, 1),
        due_date=date(2023, 8, 15),
    ),
    Project(
        name="Fraud Detection",
        code="FRD-06",
        status=Status.active,
        owner="Priya Nair",
        priority=Priority.high,
        budget=420000.0,
        progress=71,
        active=True,
        start_date=date(2024, 3, 18),
        due_date=date(2025, 1, 31),
    ),
    Project(
        name="Green Reporting",
        code="GRN-07",
        status=Status.planned,
        owner="Thomas Berg",
        priority=Priority.medium,
        budget=76000.0,
        progress=0,
        active=True,
        start_date=date(2024, 9, 1),
        due_date=date(2025, 6, 30),
    ),
    Project(
        name="HR Self-Service",
        code="HR-08",
        status=Status.active,
        owner="Clara Meyer",
        priority=Priority.low,
        budget=68000.0,
        progress=54,
        active=True,
        start_date=date(2024, 2, 12),
        due_date=date(2024, 11, 15),
    ),
    Project(
        name="Inventory Sync",
        code="INV-09",
        status=Status.done,
        owner="Diego García",
        priority=Priority.medium,
        budget=133000.0,
        progress=100,
        active=False,
        start_date=date(2022, 10, 3),
        due_date=date(2023, 7, 1),
    ),
    Project(
        name="Kiosk Platform",
        code="KIO-10",
        status=Status.active,
        owner="Kenji Tanaka",
        priority=Priority.high,
        budget=205000.0,
        progress=39,
        active=True,
        start_date=date(2024, 4, 22),
        due_date=date(2025, 2, 28),
    ),
]


projects = c.DataPage(
    routes=router,
    path="/data-page",
    source=SimpleDataSource(PROJECTS),
    type=Project,
    type_name="Project",
    page_title="Projects",
)

# Convenience handle for the app's navigation wiring.
page = projects.page
