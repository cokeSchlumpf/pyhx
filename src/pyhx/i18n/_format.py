"""Formatting numbers, dates and times in the language and timezone of the request.

Thin wrappers of Babel's functions: the language defaults to
:func:`~pyhx.core.primitives.negotiate_locale`, the display timezone to
:func:`~pyhx.core.primitives.negotiate_timezone`. Pass ``locale`` (or
``tzinfo``) only to pin a value. The data tables use the same functions.
"""

from datetime import UTC, date, datetime, time, tzinfo
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from babel.dates import format_date as _babel_date
from babel.dates import format_datetime as _babel_datetime
from babel.dates import format_time as _babel_time
from babel.dates import format_timedelta as _babel_timedelta
from babel.numbers import format_compact_decimal as _babel_compact
from babel.numbers import format_currency as _babel_currency
from babel.numbers import format_decimal as _babel_decimal
from babel.numbers import format_percent as _babel_percent

from pyhx.core.primitives import negotiate_locale, negotiate_timezone

type Number = int | float | Decimal
type Width = Literal["short", "medium", "long", "full"]


def _in_display_zone(
    value: datetime, display: tzinfo | None, source_timezone: str
) -> datetime:
    """Move ``value`` into the display zone; a naive value is read as ``source_timezone``."""
    aware = (
        value
        if value.tzinfo is not None
        else value.replace(tzinfo=ZoneInfo(source_timezone))
    )
    return aware.astimezone(display or ZoneInfo(negotiate_timezone()))


def format_number(
    value: Number,
    format: str | None = None,
    *,
    compact: bool = False,
    locale: str | None = None,
) -> str:
    """Format a number, e.g. ``1234.5`` → ``"1.234,5"`` in German.

    Parameters
    ----------
    value
        The number.
    format
        A Babel number pattern, e.g. ``"#,##0.00"``; default: the language's.
    compact
        Short form, e.g. ``"1.2K"``.
    locale
        Pins the language; default: the request's.
    """
    locale = locale or negotiate_locale()
    if compact:
        return _babel_compact(value, format_type="short", locale=locale)
    return _babel_decimal(value, format=format, locale=locale)


def format_currency(value: Number, currency: str, *, locale: str | None = None) -> str:
    """Format an amount, e.g. ``(1234.5, "EUR")`` → ``"1.234,50 €"`` in German."""
    return _babel_currency(value, currency, locale=locale or negotiate_locale())


def format_percent(
    value: Number, format: str | None = None, *, locale: str | None = None
) -> str:
    """Format a ratio as percent, e.g. ``0.25`` → ``"25 %"`` in German."""
    return _babel_percent(value, format=format, locale=locale or negotiate_locale())


def format_date(
    value: date,
    format: Width | str = "medium",
    *,
    locale: str | None = None,
    tzinfo: tzinfo | None = None,
    source_timezone: str = "UTC",
) -> str:
    """Format a date; a ``datetime`` is first moved into the display timezone.

    Parameters
    ----------
    value
        A ``date``, or a ``datetime`` (naive values are read as ``source_timezone``).
    format
        ``"short"``, ``"medium"``, ``"long"``, ``"full"`` or a Babel pattern.
    locale
        Pins the language; default: the request's.
    tzinfo
        Pins the display timezone; default: the request's.
    source_timezone
        Timezone of naive datetimes.
    """
    if isinstance(value, datetime):
        value = _in_display_zone(value, tzinfo, source_timezone)
    return _babel_date(value, format=format, locale=locale or negotiate_locale())


def format_datetime(
    value: date,
    format: Width | str = "medium",
    *,
    locale: str | None = None,
    tzinfo: tzinfo | None = None,
    source_timezone: str = "UTC",
) -> str:
    """Format a date and time in the display timezone; a bare ``date`` counts as midnight."""
    moment = value if isinstance(value, datetime) else datetime.combine(value, time.min)
    moment = _in_display_zone(moment, tzinfo, source_timezone)
    return _babel_datetime(moment, format=format, locale=locale or negotiate_locale())


def format_time(
    value: datetime | time,
    format: Width | str = "short",
    *,
    locale: str | None = None,
    tzinfo: tzinfo | None = None,
    source_timezone: str = "UTC",
) -> str:
    """Format a time; a ``datetime`` is first moved into the display timezone."""
    if isinstance(value, datetime):
        value = _in_display_zone(value, tzinfo, source_timezone)
    return _babel_time(value, format=format, locale=locale or negotiate_locale())


def format_relative_time(
    value: date,
    *,
    now: datetime | None = None,
    locale: str | None = None,
    source_timezone: str = "UTC",
) -> str:
    """Format a moment relative to now, e.g. ``"vor 3 Stunden"`` or ``"in 2 days"``.

    Parameters
    ----------
    value
        A ``datetime`` (naive values are read as ``source_timezone``), or a
        ``date`` (midnight).
    now
        The reference; default: the current time.
    locale
        Pins the language; default: the request's.
    source_timezone
        Timezone of naive datetimes.
    """
    moment = value if isinstance(value, datetime) else datetime.combine(value, time.min)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo(source_timezone))
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    return _babel_timedelta(
        moment - reference, add_direction=True, locale=locale or negotiate_locale()
    )
