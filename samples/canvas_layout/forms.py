"""Forms in the canvas design: every control in every state.

Included by :mod:`samples.canvas_layout.main`. ``/forms`` shows

- a case form built with ``DataForm`` in the main column of a split layout,
- a compact correction form in its aside, and
- a grid of the controls in every state below (default, error, success,
  read-only, disabled; hover and focus with mouse and keyboard).
"""

from datetime import date
from functools import partial
from typing import Annotated, Literal

import htpy as y
from pydantic import BaseModel, Field

import pyhx.components as c
from pyhx.components import annotations as a
from pyhx.components.view_model import Option
from pyhx.core import WebAppRouter
from pyhx.core.primitives import styles

router = WebAppRouter()

STATUS_OPTIONS = (
    Option(label="Offen", value="open"),
    Option(label="In Bearbeitung", value="in_progress"),
    Option(label="Abgeschlossen", value="closed"),
)

SOURCE_OPTIONS = (
    Option(label="Hausarzt", value="gp"),
    Option(label="Selbstangabe", value="self"),
)

VIEW_OPTIONS = (
    Option(label="Liste", value="list"),
    Option(label="Karten", value="cards"),
    Option(label="Zeitachse", value="timeline"),
)


@a.form(columns=2, submit_label="Speichern")
class CaseForm(BaseModel):
    """The fields of a case, as an app on the canvas design would edit them."""

    case_number: Annotated[
        str,
        Field(min_length=3),
        a.TextField(
            label="Fallnummer",
            control=a.InputControl(placeholder="CS-2026-0001"),
        ),
    ] = "CS-2026-0142"

    status: Annotated[
        Literal["open", "in_progress", "closed"],
        a.TextChoiceField(
            label="Status", control=a.DropdownControl(options=STATUS_OPTIONS)
        ),
    ] = "in_progress"

    client_number: Annotated[
        str,
        Field(pattern=r"^\d{8}$"),
        a.TextField(label="Klientennummer", help_text="8 Ziffern, z. B. 75197814"),
    ] = ""

    received: Annotated[date, a.DateField(label="Eingang")] = date(2026, 6, 21)

    client_name: Annotated[
        str,
        Field(min_length=2),
        a.TextField(label="Name der Klientin / des Klienten", columns=2),
    ] = "David Meier"

    note: Annotated[
        str,
        a.TextField(
            label="Notiz",
            control=a.TextareaControl(rows="3"),
            help_text="Nur intern sichtbar.",
            columns=2,
        ),
    ] = ""

    urgent: Annotated[
        bool,
        a.BooleanField(
            label="Priorität",
            control=a.BooleanCheckboxFieldsetControl(label="Priorität hoch"),
        ),
    ] = False


async def _handle_case_submit(value: CaseForm) -> y.Node:
    return c.message(f"Fall {value.case_number} gespeichert.", appearance="success")


_case_form = c.DataForm[CaseForm](
    name="case",
    routes=router,
    type=CaseForm,
    handle_submit=_handle_case_submit,
)


def _select(**kwargs) -> y.Node:
    """``form_field`` factory for a native ``<select>`` with the status options."""
    value = kwargs.pop("value", None)
    return y.select(**kwargs)[
        (
            y.option(value=o.value, selected=o.value == value)[o.label]
            for o in STATUS_OPTIONS
        )
    ]


def _correction() -> y.Node:
    """Compact correction form in the aside, as in a document review."""
    return c.card[
        c.card.header[
            c.card.title[y.h2["Beginn Arbeitsunfähigkeit"]],
            c.pill("unsicher gelesen", appearance="warning", variant="outline"),
        ],
        c.card.section[
            y.form[
                c.form_field("value", "Wert", y.input, value="100% seit 28.04.2026"),
                c.radio_fieldset("Quelle", "source", SOURCE_OPTIONS, value="gp"),
                y.div(**styles("flex", "gap-sm", "items-center"))[
                    c.button(
                        "Korrektur speichern",
                        appearance="primary",
                        size="sm",
                        type="submit",
                        style="width: auto",  # Pico stretches submit buttons
                    ),
                    c.button("Abbrechen", variant="link", size="sm", type="button"),
                ],
            ]
        ],
    ]


def _column(title: str, *fields: y.Node) -> y.Node:
    return y.div[y.p(**styles("font-semibold", "mb-sm"))[title], *fields]


def _states() -> y.Node:
    """Every control in every state that markup can show."""
    return c.card[
        c.card.header[
            c.card.title[y.h2["Zustände"]],
            c.card.subtitle["Hover und Fokus mit Maus und Tastatur ausprobieren."],
        ],
        c.card.section[
            y.div(
                **styles("hx-grid"),
                style="grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr))",
            )[
                _column(
                    "Standard",
                    c.form_field(
                        "t1", "Name", y.input, placeholder="Vor- und Nachname"
                    ),
                    c.form_field("s1", "Status", _select, value="open"),
                    c.form_field("n1", "Notiz", c.textarea_input, rows="2"),
                ),
                _column(
                    "Fehler",
                    c.form_field(
                        "t2", "Name", y.input, required=True, error_text="Pflichtfeld"
                    ),
                    c.form_field("s2", "Status", _select, error_text="Status wählen"),
                    c.form_field(
                        "n2",
                        "Notiz",
                        c.textarea_input,
                        rows="2",
                        value="x",
                        error_text="Mindestens 10 Zeichen",
                    ),
                ),
                _column(
                    "Erfolg",
                    c.form_field(
                        "t3",
                        "Name",
                        y.input,
                        value="David Meier",
                        success_text="Gültig",
                    ),
                    c.form_field(
                        "s3",
                        "Status",
                        _select,
                        value="in_progress",
                        success_text="Gültig",
                    ),
                    c.form_field(
                        "n3",
                        "Notiz",
                        c.textarea_input,
                        rows="2",
                        value="Arztbericht folgt.",
                        success_text="Gültig",
                    ),
                ),
                _column(
                    "Nur lesen",
                    c.form_field(
                        "t4", "Fallnummer", y.input, value="CS-2026-0142", readonly=True
                    ),
                    c.form_field(
                        "s4", "Status", _select, value="closed", disabled=True
                    ),
                    c.form_field(
                        "n4",
                        "Notiz",
                        c.textarea_input,
                        rows="2",
                        value="Arztbericht folgt.",
                        readonly=True,
                    ),
                ),
                _column(
                    "Deaktiviert",
                    c.form_field(
                        "t5", "Name", y.input, value="David Meier", disabled=True
                    ),
                    c.form_field("s5", "Status", _select, value="open", disabled=True),
                    c.form_field(
                        "n5",
                        "Notiz",
                        c.textarea_input,
                        rows="2",
                        value="Gesperrt",
                        disabled=True,
                    ),
                ),
            ],
            y.hr,
            y.div(
                **styles("hx-grid"),
                style="grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr))",
            )[
                c.checkbox_fieldset(
                    "Benachrichtigen", "notify", SOURCE_OPTIONS, value=("gp",)
                ),
                c.radio_fieldset(
                    "Quelle", "source-states", SOURCE_OPTIONS, value="self"
                ),
                y.div[
                    y.p(**styles("font-semibold", "mb-sm"))["Schalter"],
                    y.div(**styles("flex", "flex-col", "gap-sm"))[
                        y.label[c.switch(checked=False, name="sw1"), " Aus"],
                        y.label[c.switch(checked=True, name="sw2"), " Ein"],
                        y.label[
                            c.switch(checked=True, name="sw3", disabled=True),
                            " Deaktiviert",
                        ],
                    ],
                ],
                c.checkbox_fieldset(
                    "Deaktiviert",
                    "notify-off",
                    SOURCE_OPTIONS,
                    value=("gp",),
                    disabled=True,
                ),
            ],
            y.hr,
            y.div(
                **styles("hx-grid"),
                style="grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr))",
            )[
                c.form_field(
                    "view",
                    "Ansicht",
                    partial(c.segment_control, options=VIEW_OPTIONS),
                    value="list",
                ),
                c.form_field(
                    "status-dropdown",
                    "Status (Dropdown)",
                    partial(c.dropdown_radio, options=STATUS_OPTIONS),
                    value="open",
                    help_text="Dropdown von pyhx statt nativem Select",
                ),
            ],
            y.hr,
            y.div(**styles("flex", "gap-sm", "items-center", "flex-wrap"))[
                c.button("Speichern", appearance="primary"),
                c.button("Exportieren", variant="outline"),
                c.button("Entwurf", variant="ghost"),
                c.button("Abbrechen", variant="link"),
                c.button("Fall löschen", appearance="danger", variant="outline"),
                c.button("Gesperrt", appearance="primary", disabled=True),
                c.button("Bestätigen", appearance="primary", size="sm"),
                c.button("Korrigieren", variant="outline", size="sm"),
            ],
        ],
    ]


@router.page("/forms", title="Formulare")
async def forms_page() -> y.Node:
    return y.div(**styles("flex", "flex-col", "gap-md"))[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Formulare"),
        c.split_layout(
            main=c.card[
                c.card.header[c.card.title[y.h1["Fall bearbeiten"]]],
                c.card.section[await _case_form.render()],
            ],
            aside=_correction(),
        ),
        _states(),
    ]
