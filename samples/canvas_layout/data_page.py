"""DataPages in the canvas design.

Two pages over the same in-memory list of cases, to try ``DataPage`` inside
``CanvasShell``:

- ``/data-page`` — the standard: a row click opens the built-in edit drawer
  (form, cancel, delete), the create button opens the create drawer. Fits
  small records that are edited as a form.
- ``/data-page-detail`` — a row click opens the case's detail page instead of
  the drawer (``can_edit`` as a callable); its create drawer keeps the labels
  above the fields and the model's two columns (``form_label_position="top"``). Fits records that are a workspace
  rather than a form, like a case with documents; the sample links every row
  to the dossier page.

The create/edit/delete actions mutate a ``SimpleDataSource`` list, so no
backend is needed.
"""

from datetime import date
from enum import Enum
from typing import Annotated

import htpy as y
from commons.id_operators import new_id
from pydantic import BaseModel, Field

import pyhx.components as c
import pyhx.components.data.annotations as a
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core import WebAppRouter
from pyhx.core.fragment import FragmentResponse

router = WebAppRouter()


class CaseStatus(str, Enum):
    new = "Neu"
    in_progress = "In Bearbeitung"
    requires_input = "Eingabe erforderlich"
    closed = "Abgeschlossen"


@a.form(columns=2)
class Case(BaseModel):
    """One model for the table, the create form and the edit form."""

    id: Annotated[str, a.HiddenColumn(), a.HiddenField()] = Field(
        default_factory=new_id
    )
    case_number: Annotated[str, a.TextColumn(label="Fallnummer")]
    client_name: Annotated[str, a.TextColumn(label="Versicherte Person")]
    client_number: Annotated[str, a.TextColumn(label="AHV-Nr.")]
    status: Annotated[CaseStatus, a.TextColumn(label="Status")]
    received: Annotated[date, a.DateColumn(label="Eingang")]
    documents: Annotated[int, a.NumericColumn(label="Dokumente")]


def _cases() -> list[Case]:
    return [
        Case(
            case_number=number,
            client_name=name,
            client_number=ahv,
            status=status,
            received=received,
            documents=documents,
        )
        for number, name, ahv, status, received, documents in (
            (
                "IV-2026-0142",
                "David Meier",
                "756.1978.0814.05",
                CaseStatus.new,
                date(2026, 3, 15),
                3,
            ),
            (
                "IV-2026-0139",
                "Sandra Keller",
                "756.1985.2203.17",
                CaseStatus.in_progress,
                date(2026, 3, 9),
                7,
            ),
            (
                "IV-2026-0131",
                "Marco Bianchi",
                "756.1969.0507.42",
                CaseStatus.requires_input,
                date(2026, 2, 24),
                5,
            ),
            (
                "IV-2026-0127",
                "Aylin Demir",
                "756.1991.1130.08",
                CaseStatus.in_progress,
                date(2026, 2, 17),
                11,
            ),
            (
                "IV-2026-0118",
                "Peter Huber",
                "756.1958.0619.63",
                CaseStatus.closed,
                date(2026, 1, 30),
                14,
            ),
            (
                "IV-2026-0112",
                "Laura Frei",
                "756.1999.0402.21",
                CaseStatus.new,
                date(2026, 1, 22),
                1,
            ),
            (
                "IV-2026-0104",
                "Jonas Weber",
                "756.1976.0912.84",
                CaseStatus.requires_input,
                date(2026, 1, 12),
                6,
            ),
            (
                "IV-2025-0988",
                "Fatima Rossi",
                "756.1982.0725.39",
                CaseStatus.closed,
                date(2025, 12, 3),
                9,
            ),
        )
    ]


breadcrumbs: list[y.Node] = [y.a(href="/")["Canvas Layout"]]

cases: c.DataPage[Case, Case, Case, Case] = c.DataPage(
    routes=router,
    path="/data-page",
    source=SimpleDataSource(_cases()),
    type=Case,
    name="cases_drawer",
    type_name="Fall",
    page_title="Fälle",
    breadcrumbs=breadcrumbs,
    create_button_label="Fall erfassen",
    create_dialog_title="Fall erfassen",
    edit_dialog_title="Fall bearbeiten",
    create_submit_label="Erfassen",
    edit_submit_label="Speichern",
    cancel_create_label="Abbrechen",
    cancel_edit_label="Abbrechen",
    delete_item_label="Fall löschen",
)


async def _open_case(case: Case) -> FragmentResponse:
    """Row click: open the case's detail page instead of the edit drawer."""
    return FragmentResponse.redirect("/dossier")


cases_detail: c.DataPage[Case, Case, Case, Case] = c.DataPage(
    routes=router,
    path="/data-page-detail",
    source=SimpleDataSource(_cases()),
    type=Case,
    name="cases_detail",
    type_name="Fall",
    page_title="Fälle (Detailseite)",
    breadcrumbs=breadcrumbs,
    create_button_label="Fall erfassen",
    create_dialog_title="Fall erfassen",
    create_submit_label="Erfassen",
    cancel_create_label="Abbrechen",
    form_label_position="top",
    can_edit=_open_case,
)
