"""`DateTimeColumn` — auto-derivation for `datetime` fields, relative-by-default
rendering, and day-granularity date filtering over `datetime` cell values."""

from datetime import date, datetime, timezone
from typing import Annotated

from pydantic import BaseModel

from pyhx.components.data.annotations.column import (
    DateTimeColumn,
    IsoDateFormat,
)
from pyhx.components.data.annotations.reader import read_column_annotations
from pyhx.components.data.sources._query import _matches_value
from pyhx.components.data.sources.filter import (
    DateAfter,
    DateBefore,
    DateBetween,
    DateEquals,
)
from pyhx.components.data.sources.filter_type import DateFilter as DateFilterT
from pyhx.core.request_context import RequestContext, set_request_context


def _clear_request() -> None:
    set_request_context(RequestContext())


# ---------------------------------------------------------------------------
# Auto-derivation: a bare `datetime` field
# ---------------------------------------------------------------------------


class AutoModel(BaseModel):
    created: datetime


def test_bare_datetime_field_is_auto_derived():
    cols = read_column_annotations(AutoModel)
    assert "created" in cols  # not silently skipped


def test_auto_derived_datetime_has_date_filter():
    cols = read_column_annotations(AutoModel)
    assert isinstance(cols["created"].filter_type, DateFilterT)


def test_auto_derived_datetime_uses_date_kind():
    cols = read_column_annotations(AutoModel)
    assert cols["created"].kind == "date"


def test_auto_derived_datetime_renders_relative_by_default():
    _clear_request()
    cols = read_column_annotations(AutoModel)
    row = AutoModel(created=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    rendered = str(cols["created"].render(row))
    assert "ago" in rendered  # RelativeDateFormat is the default


# ---------------------------------------------------------------------------
# Explicit DateTimeColumn
# ---------------------------------------------------------------------------


class ExplicitModel(BaseModel):
    at: Annotated[datetime, DateTimeColumn(label="At", format=IsoDateFormat())]


def test_explicit_datetime_column_maps_to_date_filter():
    cols = read_column_annotations(ExplicitModel)
    assert isinstance(cols["at"].filter_type, DateFilterT)


def test_explicit_datetime_iso_keeps_time():
    _clear_request()
    cols = read_column_annotations(ExplicitModel)
    row = ExplicitModel(at=datetime(2024, 4, 25, 14, 30, 45, tzinfo=timezone.utc))
    assert "14:30:45" in str(cols["at"].render(row))


def test_datetime_filter_can_be_disabled():
    class NoFilter(BaseModel):
        at: Annotated[datetime, DateTimeColumn(filter=False)]

    cols = read_column_annotations(NoFilter)
    assert cols["at"].filter_type is None


# ---------------------------------------------------------------------------
# Filtering: datetime cell value compared against date-only thresholds.
# Regression — before/after/between used to raise TypeError, equals never matched.
# ---------------------------------------------------------------------------


_DT = datetime(2024, 4, 25, 14, 30, 45)


def test_date_equals_matches_datetime_by_calendar_day():
    assert _matches_value(_DT, DateEquals(value=date(2024, 4, 25))) is True
    assert _matches_value(_DT, DateEquals(value=date(2024, 4, 26))) is False


def test_date_before_does_not_raise_on_datetime():
    assert _matches_value(_DT, DateBefore(value=date(2024, 4, 26))) is True
    assert _matches_value(_DT, DateBefore(value=date(2024, 4, 25))) is False


def test_date_after_does_not_raise_on_datetime():
    assert _matches_value(_DT, DateAfter(value=date(2024, 4, 24))) is True
    assert _matches_value(_DT, DateAfter(value=date(2024, 4, 25))) is False


def test_date_between_does_not_raise_on_datetime():
    inside = DateBetween(min=date(2024, 4, 24), max=date(2024, 4, 26))
    outside = DateBetween(min=date(2024, 4, 26), max=date(2024, 4, 28))
    assert _matches_value(_DT, inside) is True
    assert _matches_value(_DT, outside) is False


def test_date_equals_still_works_for_plain_date():
    assert _matches_value(date(2024, 4, 25), DateEquals(value=date(2024, 4, 25))) is True
