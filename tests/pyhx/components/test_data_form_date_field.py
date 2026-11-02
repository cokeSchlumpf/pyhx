"""A ``DateField`` renders for dates, datetimes, raw text and empty values, as ``YYYY-MM-DD``."""

import asyncio
import re
from datetime import date, datetime
from typing import Annotated

import htpy as y
from pydantic import BaseModel

from pyhx.components import annotations as a
from pyhx.components.data.data_form import DataForm


class _Fragment:
    def url(self, **kwargs) -> str:
        return "/x"


class _FragmentFactory:
    def add(self, path, method, fn) -> _Fragment:
        return _Fragment()


class _Routes:
    def __init__(self) -> None:
        self.fragment = _FragmentFactory()


async def _noop(value):  # pragma: no cover - never invoked in these tests
    return y.div


class Period(BaseModel):
    starts: Annotated[date | None, a.DateField(label="Starts")] = None
    at: Annotated[datetime | None, a.DateField(label="At")] = None


def _names_with_date_input(value: object = None) -> list[str]:
    form = DataForm(routes=_Routes(), name="t", type=Period, handle_submit=_noop)  # type: ignore[arg-type]
    html = str(asyncio.run(form.render(value)))  # type: ignore[arg-type]
    return sorted(m for tag in re.findall(r'<input[^>]*type="date"[^>]*>', html) for m in re.findall(r'name="(\w+)"', tag))


def _value_of(name: str, value: object) -> str:
    form = DataForm(routes=_Routes(), name="t", type=Period, handle_submit=_noop)  # type: ignore[arg-type]
    html = str(asyncio.run(form.render(value)))  # type: ignore[arg-type]
    tag = next(t for t in re.findall(r'<input[^>]*type="date"[^>]*>', html) if f'name="{name}"' in t)
    match = re.search(r'value="([^"]*)"', tag)
    return match.group(1) if match else ""


def test_empty_date_fields_are_rendered():
    assert _names_with_date_input() == ["at", "starts"]
    assert _names_with_date_input(Period()) == ["at", "starts"]


def test_a_date_is_shown_as_iso_day():
    assert _value_of("starts", Period(starts=date(2026, 12, 1))) == "2026-12-01"


def test_a_datetime_shows_its_day():
    assert _value_of("at", Period(at=datetime(2026, 12, 1, 15, 30))) == "2026-12-01"


def test_raw_text_of_a_rerendered_form_is_kept():
    assert _value_of("starts", Period.model_construct(starts="2026-12-24")) == "2026-12-24"
