"""Render-time behaviour of the date column formatters — UTC reference for
relative time, and timezone conversion for localized dates."""

from datetime import date, datetime, timedelta, timezone

from fastapi import Request

from pyhx.components.data.annotations.column import (
    IsoDateFormat,
    LocalizedDateFormat,
    LocalizedDateTimeFormat,
    PatternDateFormat,
    RelativeDateFormat,
)
from pyhx.components.data.annotations.reader import _date_value_renderer
from pyhx.core.request_context import RequestContext, set_request_context


def _render(fmt, value) -> str:
    return str(_date_value_renderer(fmt)(value))


def _install_request(*, cookies: dict[str, str] | None = None) -> None:
    """Seed a RequestContext carrying a minimal Starlette request with cookies."""
    headers = []
    if cookies:
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        headers.append((b"cookie", cookie_header.encode()))
    request = Request({"type": "http", "headers": headers})
    set_request_context(RequestContext(request=request))


def _clear_request() -> None:
    set_request_context(RequestContext())


# ---------------------------------------------------------------------------
# RelativeDateFormat — reference is now-in-UTC, naive values read as UTC
# ---------------------------------------------------------------------------


def test_relative_uses_utc_reference_for_naive_value():
    _clear_request()
    # A naive timestamp two hours before now-UTC must read as "2 hours ago"
    # regardless of the server's local timezone.
    two_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(
        tzinfo=None
    )
    assert "2 hours ago" in _render(RelativeDateFormat(), two_hours_ago)


def test_relative_respects_aware_value():
    _clear_request()
    aware = datetime.now(timezone.utc) - timedelta(minutes=30)
    assert "30 minutes ago" in _render(RelativeDateFormat(), aware)


def test_relative_source_timezone_shifts_delta():
    _clear_request()
    # Same naive wall-clock digits, read in two source zones. Reading digits
    # as a zone *ahead* of UTC means the real instant is *earlier* (Zurich
    # 10:00 == UTC 08:00), so the "ago" delta grows.
    naive = (datetime.now(timezone.utc) - timedelta(hours=3)).replace(tzinfo=None)
    as_utc = _render(RelativeDateFormat(), naive)
    as_zurich = _render(
        RelativeDateFormat(source_timezone="Europe/Zurich"), naive
    )
    assert "3 hours ago" in as_utc
    # Zurich is +1/+2h ahead of UTC → instant is 1-2h further in the past.
    assert ("5 hours ago" in as_zurich) or ("4 hours ago" in as_zurich)


def test_relative_none_renders_empty():
    _clear_request()
    assert _render(RelativeDateFormat(), None) == "<span></span>"


# ---------------------------------------------------------------------------
# LocalizedDateFormat — datetime converted into the display zone
# ---------------------------------------------------------------------------


def test_localized_datetime_crosses_midnight_in_display_zone():
    _clear_request()
    # 23:00 UTC on the 25th is already the 26th in Europe/Zurich (UTC+1/+2).
    value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
    rendered = _render(
        LocalizedDateFormat(locale="en", timezone="Europe/Zurich"), value
    )
    assert "26" in rendered


def test_localized_datetime_utc_display_keeps_day():
    _clear_request()
    value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
    rendered = _render(
        LocalizedDateFormat(locale="en", timezone="UTC"), value
    )
    assert "25" in rendered


def test_localized_bare_date_is_not_tz_shifted():
    _clear_request()
    # A plain date has no instant; the display zone must not move it.
    rendered = _render(
        LocalizedDateFormat(locale="en", timezone="Europe/Zurich"),
        date(2024, 4, 25),
    )
    assert "25" in rendered


def test_localized_display_tz_from_cookie():
    _install_request(cookies={"hx_tz": "Europe/Zurich"})
    try:
        value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
        rendered = _render(LocalizedDateFormat(locale="en"), value)
        assert "26" in rendered
    finally:
        _clear_request()


def test_localized_pinned_tz_overrides_cookie():
    _install_request(cookies={"hx_tz": "Europe/Zurich"})
    try:
        value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
        # Pinned UTC wins over the Zurich cookie → stays on the 25th.
        rendered = _render(
            LocalizedDateFormat(locale="en", timezone="UTC"), value
        )
        assert "25" in rendered
    finally:
        _clear_request()


# ---------------------------------------------------------------------------
# LocalizedDateTimeFormat — keeps the time-of-day and converts the instant
# ---------------------------------------------------------------------------


def test_localized_datetime_format_renders_time_of_day():
    _clear_request()
    value = datetime(2024, 4, 25, 14, 30, 45, tzinfo=timezone.utc)
    rendered = _render(
        LocalizedDateTimeFormat(locale="en", width="medium", timezone="UTC"), value
    )
    # `medium` includes seconds; unlike LocalizedDateFormat the time survives.
    assert "2" in rendered  # date part present
    assert "30" in rendered  # minutes
    assert "45" in rendered  # seconds


def test_localized_datetime_format_converts_instant_to_display_zone():
    _clear_request()
    # 23:00 UTC on the 25th is already 01:00 on the 26th in Zurich (UTC+2 in DST).
    value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
    rendered = _render(
        LocalizedDateTimeFormat(locale="en", timezone="Europe/Zurich"), value
    )
    assert "26" in rendered


def test_localized_datetime_display_tz_from_cookie():
    _install_request(cookies={"hx_tz": "Europe/Zurich"})
    try:
        value = datetime(2024, 4, 25, 23, 0, tzinfo=timezone.utc)
        rendered = _render(LocalizedDateTimeFormat(locale="en"), value)
        assert "26" in rendered
    finally:
        _clear_request()


def test_localized_datetime_none_renders_empty():
    _clear_request()
    assert (
        _render(LocalizedDateTimeFormat(locale="en"), None) == "<span></span>"
    )


def test_iso_and_pattern_keep_time_for_datetime():
    _clear_request()
    value = datetime(2024, 4, 25, 14, 30, 45, tzinfo=timezone.utc)
    assert "14:30:45" in _render(IsoDateFormat(), value)
    assert "14:30:45" in _render(
        PatternDateFormat(pattern="%d %b %Y %H:%M:%S"), value
    )
