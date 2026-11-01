"""Table View demo — a many-column table in App Mode.

Renders a :func:`pyhx.components.page_header` above a **full-width**
(``width="stretch"``) container holding a ``DataTable`` with ~22 columns.
Every column carries an explicit fixed width, so the grid-track total far
exceeds the viewport and the table's scroll container scrolls horizontally
instead of squishing the columns. The page uses ``mode="app"`` so the
footer stays pinned to the viewport bottom while the table scrolls.
"""

from datetime import date
from enum import Enum
from typing import Annotated

import htpy as y
import pyhx.components as c

from pydantic import BaseModel

from pyhx.core import PageResponse, WebAppRouter
from pyhx.page_templates import AppShell


router = WebAppRouter()


class Level(str, Enum):
    junior = "Junior"
    mid = "Mid"
    senior = "Senior"
    lead = "Lead"
    principal = "Principal"


class EmploymentType(str, Enum):
    full_time = "Full-time"
    part_time = "Part-time"
    contract = "Contract"


class Employee(BaseModel):
    id: Annotated[int, c.annotations.HiddenColumn()]
    first_name: Annotated[
        str, c.annotations.TextColumn(label="First name", width=c.Fixed("140px"))
    ]
    last_name: Annotated[
        str, c.annotations.TextColumn(label="Last name", width=c.Fixed("140px"))
    ]
    employee_no: Annotated[
        str, c.annotations.TextColumn(label="Emp. #", width=c.Fixed("110px"))
    ]
    email: Annotated[
        str, c.annotations.TextColumn(label="Email", width=c.Fixed("240px"))
    ]
    phone: Annotated[
        str, c.annotations.TextColumn(label="Phone", width=c.Fixed("160px"))
    ]
    department: Annotated[
        str, c.annotations.TextColumn(label="Department", width=c.Fixed("150px"))
    ]
    team: Annotated[
        str, c.annotations.TextColumn(label="Team", width=c.Fixed("150px"))
    ]
    role: Annotated[
        str, c.annotations.TextColumn(label="Role", width=c.Fixed("180px"))
    ]
    level: Annotated[
        Level, c.annotations.TextColumn(label="Level", width=c.Fixed("120px"))
    ]
    manager: Annotated[
        str, c.annotations.TextColumn(label="Manager", width=c.Fixed("170px"))
    ]
    office: Annotated[
        str, c.annotations.TextColumn(label="Office", width=c.Fixed("140px"))
    ]
    country: Annotated[
        str, c.annotations.TextColumn(label="Country", width=c.Fixed("140px"))
    ]
    timezone: Annotated[
        str, c.annotations.TextColumn(label="Timezone", width=c.Fixed("130px"))
    ]
    start_date: Annotated[
        date, c.annotations.DateColumn(label="Start date", width=c.Fixed("130px"))
    ]
    end_date: Annotated[
        date | None,
        c.annotations.DateColumn(label="End date", width=c.Fixed("130px")),
    ]
    employment_type: Annotated[
        EmploymentType,
        c.annotations.TextColumn(label="Type", width=c.Fixed("120px")),
    ]
    salary: Annotated[
        float,
        c.annotations.NumericColumn(
            label="Salary",
            width=c.Fixed("140px"),
            format=c.annotations.CurrencyNumberFormat(currency="EUR"),
        ),
    ]
    bonus_pct: Annotated[
        float,
        c.annotations.NumericColumn(
            label="Bonus %",
            width=c.Fixed("110px"),
            format=c.annotations.PatternNumberFormat.percent(),
        ),
    ]
    active: Annotated[
        bool, c.annotations.BooleanColumn(label="Active", width=c.Fixed("100px"))
    ]
    rating: Annotated[
        float, c.annotations.NumericColumn(label="Rating", width=c.Fixed("100px"))
    ]
    tags: Annotated[
        list[str],
        c.annotations.TextListColumn(label="Tags", width=c.Fixed("220px")),
    ]


EMPLOYEES: list[Employee] = [
    Employee(
        id=1,
        first_name="Anna",
        last_name="Schmidt",
        employee_no="E-1001",
        email="anna.schmidt@example.com",
        phone="+49 151 2345678",
        department="Engineering",
        team="Platform",
        role="Backend Engineer",
        level=Level.senior,
        manager="Lukas Weber",
        office="Berlin",
        country="Germany",
        timezone="CET",
        start_date=date(2019, 3, 4),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=82000.0,
        bonus_pct=0.12,
        active=True,
        rating=4.6,
        tags=["python", "aws", "mentor"],
    ),
    Employee(
        id=2,
        first_name="Marco",
        last_name="Rossi",
        employee_no="E-1002",
        email="marco.rossi@example.com",
        phone="+39 340 1122334",
        department="Engineering",
        team="Frontend",
        role="Frontend Engineer",
        level=Level.mid,
        manager="Giulia Bianchi",
        office="Milan",
        country="Italy",
        timezone="CET",
        start_date=date(2021, 9, 1),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=61000.0,
        bonus_pct=0.08,
        active=True,
        rating=4.1,
        tags=["typescript", "react"],
    ),
    Employee(
        id=3,
        first_name="Sophie",
        last_name="Martin",
        employee_no="E-1003",
        email="sophie.martin@example.com",
        phone="+33 6 55 44 33 22",
        department="Design",
        team="Product Design",
        role="Product Designer",
        level=Level.senior,
        manager="Camille Durand",
        office="Paris",
        country="France",
        timezone="CET",
        start_date=date(2018, 6, 18),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=74000.0,
        bonus_pct=0.1,
        active=True,
        rating=4.8,
        tags=["figma", "ux", "design-system"],
    ),
    Employee(
        id=4,
        first_name="James",
        last_name="Wilson",
        employee_no="E-1004",
        email="james.wilson@example.com",
        phone="+44 7700 900123",
        department="Sales",
        team="EMEA",
        role="Account Executive",
        level=Level.mid,
        manager="Emma Taylor",
        office="London",
        country="United Kingdom",
        timezone="GMT",
        start_date=date(2020, 1, 13),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=68000.0,
        bonus_pct=0.2,
        active=True,
        rating=3.9,
        tags=["saas", "enterprise"],
    ),
    Employee(
        id=5,
        first_name="Lena",
        last_name="Fischer",
        employee_no="E-1005",
        email="lena.fischer@example.com",
        phone="+49 152 9988776",
        department="Engineering",
        team="Data",
        role="Data Engineer",
        level=Level.senior,
        manager="Lukas Weber",
        office="Munich",
        country="Germany",
        timezone="CET",
        start_date=date(2017, 11, 6),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=85000.0,
        bonus_pct=0.14,
        active=True,
        rating=4.5,
        tags=["spark", "python", "etl"],
    ),
    Employee(
        id=6,
        first_name="Diego",
        last_name="García",
        employee_no="E-1006",
        email="diego.garcia@example.com",
        phone="+34 611 223344",
        department="Support",
        team="Tier 2",
        role="Support Engineer",
        level=Level.junior,
        manager="Paula Núñez",
        office="Madrid",
        country="Spain",
        timezone="CET",
        start_date=date(2022, 4, 25),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=41000.0,
        bonus_pct=0.05,
        active=True,
        rating=3.7,
        tags=["support", "sql"],
    ),
    Employee(
        id=7,
        first_name="Nadia",
        last_name="Haddad",
        employee_no="E-1007",
        email="nadia.haddad@example.com",
        phone="+31 6 12345678",
        department="Marketing",
        team="Growth",
        role="Growth Marketer",
        level=Level.mid,
        manager="Tom de Vries",
        office="Amsterdam",
        country="Netherlands",
        timezone="CET",
        start_date=date(2021, 2, 8),
        end_date=None,
        employment_type=EmploymentType.part_time,
        salary=52000.0,
        bonus_pct=0.09,
        active=True,
        rating=4.2,
        tags=["seo", "content"],
    ),
    Employee(
        id=8,
        first_name="Oliver",
        last_name="Novak",
        employee_no="E-1008",
        email="oliver.novak@example.com",
        phone="+420 601 234567",
        department="Engineering",
        team="Platform",
        role="Site Reliability Engineer",
        level=Level.lead,
        manager="Lukas Weber",
        office="Prague",
        country="Czechia",
        timezone="CET",
        start_date=date(2016, 8, 15),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=95000.0,
        bonus_pct=0.16,
        active=True,
        rating=4.7,
        tags=["kubernetes", "go", "oncall"],
    ),
    Employee(
        id=9,
        first_name="Ingrid",
        last_name="Larsen",
        employee_no="E-1009",
        email="ingrid.larsen@example.com",
        phone="+47 400 12 345",
        department="Finance",
        team="Controlling",
        role="Financial Analyst",
        level=Level.mid,
        manager="Erik Hansen",
        office="Oslo",
        country="Norway",
        timezone="CET",
        start_date=date(2019, 10, 1),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=71000.0,
        bonus_pct=0.11,
        active=True,
        rating=4.0,
        tags=["excel", "forecasting"],
    ),
    Employee(
        id=10,
        first_name="Kenji",
        last_name="Tanaka",
        employee_no="E-1010",
        email="kenji.tanaka@example.com",
        phone="+81 90 1234 5678",
        department="Engineering",
        team="Mobile",
        role="Mobile Engineer",
        level=Level.senior,
        manager="Giulia Bianchi",
        office="Tokyo",
        country="Japan",
        timezone="JST",
        start_date=date(2018, 1, 22),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=88000.0,
        bonus_pct=0.13,
        active=True,
        rating=4.4,
        tags=["swift", "kotlin"],
    ),
    Employee(
        id=11,
        first_name="Priya",
        last_name="Nair",
        employee_no="E-1011",
        email="priya.nair@example.com",
        phone="+91 98765 43210",
        department="Product",
        team="Core",
        role="Product Manager",
        level=Level.lead,
        manager="Emma Taylor",
        office="Bangalore",
        country="India",
        timezone="IST",
        start_date=date(2017, 5, 30),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=79000.0,
        bonus_pct=0.18,
        active=True,
        rating=4.6,
        tags=["roadmap", "discovery"],
    ),
    Employee(
        id=12,
        first_name="Thomas",
        last_name="Berg",
        employee_no="E-1012",
        email="thomas.berg@example.com",
        phone="+46 70 123 45 67",
        department="Engineering",
        team="Platform",
        role="Engineering Manager",
        level=Level.principal,
        manager="—",
        office="Stockholm",
        country="Sweden",
        timezone="CET",
        start_date=date(2015, 3, 2),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=112000.0,
        bonus_pct=0.22,
        active=True,
        rating=4.9,
        tags=["leadership", "architecture"],
    ),
    Employee(
        id=13,
        first_name="Clara",
        last_name="Meyer",
        employee_no="E-1013",
        email="clara.meyer@example.com",
        phone="+49 160 5566778",
        department="HR",
        team="People Ops",
        role="HR Business Partner",
        level=Level.mid,
        manager="Sabine Vogel",
        office="Hamburg",
        country="Germany",
        timezone="CET",
        start_date=date(2020, 7, 20),
        end_date=None,
        employment_type=EmploymentType.full_time,
        salary=63000.0,
        bonus_pct=0.07,
        active=True,
        rating=4.1,
        tags=["hr", "hiring"],
    ),
    Employee(
        id=14,
        first_name="Pieter",
        last_name="Jansen",
        employee_no="E-1014",
        email="pieter.jansen@example.com",
        phone="+32 470 12 34 56",
        department="Sales",
        team="Benelux",
        role="Sales Development Rep",
        level=Level.junior,
        manager="James Wilson",
        office="Brussels",
        country="Belgium",
        timezone="CET",
        start_date=date(2023, 2, 6),
        end_date=None,
        employment_type=EmploymentType.contract,
        salary=45000.0,
        bonus_pct=0.15,
        active=True,
        rating=3.6,
        tags=["outbound"],
    ),
    Employee(
        id=15,
        first_name="Yuki",
        last_name="Sato",
        employee_no="E-1015",
        email="yuki.sato@example.com",
        phone="+81 80 9876 5432",
        department="Design",
        team="Brand",
        role="Visual Designer",
        level=Level.mid,
        manager="Camille Durand",
        office="Osaka",
        country="Japan",
        timezone="JST",
        start_date=date(2021, 11, 15),
        end_date=date(2024, 6, 30),
        employment_type=EmploymentType.contract,
        salary=58000.0,
        bonus_pct=0.06,
        active=False,
        rating=4.3,
        tags=["branding", "illustration"],
    ),
]


_table = c.DataTable[Employee](
    routes=router,
    name="employees",
    source=EMPLOYEES,
    type=Employee,
    # Gives the table its own hx-table__scroll-container; the app-shell's
    # table-only app-page layout flex-fills that container so the table scrolls
    # internally (fixed header + pinned toolbar) instead of the page scrolling.
    scrollable=True,
)


@router.page("/table-view", title="Table View")
async def table_view() -> PageResponse:
    return PageResponse(
        node=y.fragment[
            c.page_header(
                title=y.h1["Table View"],
                actions=y.fragment[
                    c.pill(f"{len(EMPLOYEES)} employees"),
                    c.button("Export"),
                    c.button("Add employee", appearance="primary"),
                ],
            ),
            c.container(
                await _table.render(),
                width="stretch",
            ),
        ],
        page_template=AppShell(mode="app", compact_main_navigation=False),
    )
