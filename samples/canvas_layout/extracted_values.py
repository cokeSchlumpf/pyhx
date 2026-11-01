"""Editable extracted values of the dossier page (``InlineEdit``).

Included by :mod:`samples.canvas_layout.main`. The values extracted from the
documents of a dossier are corrected one at a time, in place, while the
documents stay visible: the four values of the card "Extrahierte Angaben"
and the reading of the doctor's report in the aside ("Zu prüfen").

The values live in an in-memory store (``STORE``), keyed by the dossier's
case number; a corrected value is marked as such in its source line.
"""

import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypedDict
from zoneinfo import ZoneInfo

import htpy as y
from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

import pyhx.components as c
from pyhx.core import WebAppRouter

router = WebAppRouter()

DOSSIER = "IV-2026-0142"


@dataclass
class _Dossier:
    """Extracted values of one dossier; ``corrected`` names the edited ones."""

    activity: str = "Bauleiter"
    workload: int = 100
    incapacity_start: datetime.date = datetime.date(2026, 1, 20)
    incapacity_degree: int = 100
    report_degree: int = 100
    report_since: datetime.date = datetime.date(2026, 4, 28)
    corrected: set[str] = field(default_factory=set)


STORE: dict[str, _Dossier] = {DOSSIER: _Dossier()}


def _percent(value: int) -> int:
    if not 0 <= value <= 100:
        raise PydanticCustomError("percent", "Zwischen 0 und 100 %")
    return value


def _not_in_future(value: datetime.date) -> datetime.date:
    if value > datetime.datetime.now(tz=ZoneInfo("Europe/Zurich")).date():
        raise PydanticCustomError("future", "Darf nicht in der Zukunft liegen")
    return value


class Activity(BaseModel):
    value: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise PydanticCustomError("empty", "Bitte eine Tätigkeit angeben")
        return value


class Percent(BaseModel):
    value: int

    _check = field_validator("value")(_percent)


class StartDate(BaseModel):
    value: datetime.date

    _check = field_validator("value")(_not_in_future)


class Reading(BaseModel):
    """Degree and start of the incapacity as read from the doctor's report."""

    degree: int = Field(title="Grad in %")
    since: datetime.date = Field(title="Seit")

    _check_degree = field_validator("degree")(_percent)
    _check_since = field_validator("since")(_not_in_future)


def _date(value: datetime.date) -> str:
    return value.strftime("%d.%m.%Y")


def _source(attribute: str, document: str) -> Callable[[str, object], y.Node]:
    """Source line: the document, marked once the value was corrected."""

    def render(key: str, value: object) -> y.Node:
        link = y.a(href="#")[document]
        if attribute in STORE[key].corrected:
            return ["Korrigiert · ", link]
        return link

    return render


class _Labels(TypedDict):
    save_label: str
    cancel_label: str
    edit_label: str
    shortcuts_hint: str


_LABELS: _Labels = {
    "save_label": "Korrektur speichern",
    "cancel_label": "Abbrechen",
    "edit_label": "Bearbeiten",
    "shortcuts_hint": "Esc abbrechen · ↵ speichern",
}


def _single[T: Activity | Percent | StartDate](
    attribute: str,
    model: type[T],
    label: str,
    document: str,
    display: Callable[[T], y.Node] | None = None,
) -> c.InlineEdit[T]:
    """An ``InlineEdit`` for one attribute of the dossier."""

    async def load(key: str) -> T:
        return model(value=getattr(STORE[key], attribute))

    async def save(key: str, value: T) -> T:
        setattr(STORE[key], attribute, value.value)
        STORE[key].corrected.add(attribute)
        return value

    return c.InlineEdit[T](
        routes=router,
        name=attribute,
        type=model,
        label=label,
        load=load,
        save=save,
        display=display,
        source=_source(attribute, document),
        **_LABELS,
    )


activity = _single("activity", Activity, "Tätigkeit", "Anmeldung S. 9")
workload = _single(
    "workload", Percent, "Pensum", "Anmeldung S. 9", lambda v: f"{v.value}%"
)
incapacity_start = _single(
    "incapacity_start",
    StartDate,
    "Beginn AU",
    "Anmeldung S. 6",
    lambda v: _date(v.value),
)
incapacity_degree = _single(
    "incapacity_degree", Percent, "Grad AU", "Anmeldung S. 6", lambda v: f"{v.value}%"
)


async def _load_reading(key: str) -> Reading:
    dossier = STORE[key]
    return Reading(degree=dossier.report_degree, since=dossier.report_since)


async def _save_reading(key: str, value: Reading) -> Reading:
    dossier = STORE[key]
    dossier.report_degree, dossier.report_since = value.degree, value.since
    dossier.corrected.add("reading")
    return value


reading = c.InlineEdit[Reading](
    routes=router,
    name="reading",
    type=Reading,
    label="Beginn Arbeitsunfähigkeit",
    load=_load_reading,
    save=_save_reading,
    display=lambda v: f"{v.degree}% seit {_date(v.since)}",
    hint=lambda key, v: (
        None if "reading" in STORE[key].corrected else "unsicher gelesen"
    ),
    source=_source("reading", "Arztbericht S. 6"),
    **_LABELS,
)


async def extracted_values_card(key: str = DOSSIER) -> y.Node:
    """The card "Extrahierte Angaben": four values, one group."""
    values = (activity, workload, incapacity_start, incapacity_degree)
    return c.card(open=True)[
        c.card.header[
            c.card.title[y.h2["Extrahierte Angaben"]],
            c.pill(str(len(values)), appearance="neutral", size="sm"),
            c.card.subtle[
                "Im Dokument attestiert oder angegeben, je mit Quelle und Seite",
            ],
        ],
        c.card.list(data_hx_inline_edit_group="extracted")[
            [c.card.item[await value.render(key)] for value in values]
        ],
    ]


async def review_card(key: str = DOSSIER) -> y.Node:
    """Aside card "Zu prüfen": a reading to check against the document."""
    return c.card[
        c.card.header[
            c.card.title[y.h2["Zu prüfen"]],
            c.card.subtle["Arztbericht Dr. Keller"],
        ],
        c.card.section(data_hx_inline_edit_group="review")[await reading.render(key)],
    ]
