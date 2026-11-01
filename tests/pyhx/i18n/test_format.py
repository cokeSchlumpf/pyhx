from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from commons.users import AnonymousUser
from starlette.requests import Request

from pyhx.components.data.annotations.column import (
    LocalizedNumberFormat,
    RelativeDateFormat,
)
from pyhx.components.data.annotations.reader import (
    _date_value_renderer,
    _number_value_renderer,
)
from pyhx.core.request_context import RequestContext
from pyhx.i18n import (
    format_currency,
    format_date,
    format_datetime,
    format_number,
    format_percent,
    format_relative_time,
    format_time,
    use_locale,
)

ZURICH = ZoneInfo("Europe/Zurich")


def _context_with(
    *, session: dict | None = None, cookie: str | None = None
) -> RequestContext:
    headers = [(b"cookie", cookie.encode())] if cookie else []
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "query_string": b"",
    }
    if session is not None:
        scope["session"] = session
    return RequestContext(request=Request(scope), user=AnonymousUser())


class TestNumbers:
    def test_number_in_the_request_language(self):
        with use_locale("de"):
            assert format_number(1234.5) == "1.234,5"
        with use_locale("en"):
            assert format_number(1234.5) == "1,234.5"

    def test_pattern_compact_and_pinned_locale(self):
        with use_locale("de"):
            assert format_number(Decimal("2"), "#,##0.00") == "2,00"
            assert format_number(1200, compact=True, locale="en") == "1K"

    def test_currency_and_percent(self):
        with use_locale("de"):
            assert format_currency(1234.5, "EUR") == "1.234,50\xa0€"
            assert format_percent(0.25) == "25\xa0%"


class TestDates:
    def test_date_in_the_request_language(self):
        with use_locale("fr"):
            assert format_date(date(2026, 11, 1), "long") == "1 novembre 2026"

    def test_datetime_moved_into_the_request_timezone(self, set_context):
        set_context(_context_with(cookie="hx_tz=Europe/Zurich"))
        with use_locale("de"):
            # 23:30 UTC is already the next day in Zurich.
            assert (
                format_date(datetime(2026, 11, 1, 23, 30, tzinfo=UTC)) == "02.11.2026"
            )
            assert (
                format_datetime(datetime(2026, 11, 1, 23, 30), "short")
                == "02.11.26, 00:30"
            )
            assert format_time(datetime(2026, 11, 1, 23, 30, tzinfo=UTC)) == "00:30"

    def test_pinned_timezone_and_plain_time(self):
        with use_locale("en"):
            assert format_time(time(9, 5)) == "9:05 AM"
            assert (
                format_date(datetime(2026, 11, 1, 23, 30, tzinfo=UTC), tzinfo=UTC)
                == "Nov 1, 2026"
            )


class TestRelativeTime:
    @pytest.mark.parametrize(
        ("locale", "expected"),
        [
            ("en", "3 hours ago"),
            ("de", "vor 3 Stunden"),
            ("it", "3 ore fa"),
            ("fr", "il y a 3 heures"),
        ],
    )
    def test_past_per_language(self, locale, expected):
        now = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
        with use_locale(locale):
            text = format_relative_time(now - timedelta(hours=3), now=now)
        assert text.replace("\xa0", " ").replace("\u202f", " ") == expected

    def test_future_and_naive_values(self):
        now = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
        with use_locale("en"):
            assert (
                format_relative_time(datetime(2026, 11, 3, 12, 0), now=now)
                == "in 2 days"
            )


class TestDataTablesUseTheRequestLanguage:
    def test_number_cell_follows_the_session_language(self, set_context):
        set_context(_context_with(session={"pyhx.locale": "de"}))

        assert (
            str(_number_value_renderer(LocalizedNumberFormat())(1234.5))
            == "<span>1.234,5</span>"
        )

    def test_pinned_locale_still_wins(self, set_context):
        set_context(_context_with(session={"pyhx.locale": "de"}))

        assert (
            str(_number_value_renderer(LocalizedNumberFormat(locale="en"))(1234.5))
            == "<span>1,234.5</span>"
        )

    def test_relative_cell_follows_the_session_language(self, set_context):
        set_context(_context_with(session={"pyhx.locale": "de"}))

        html = str(
            _date_value_renderer(RelativeDateFormat())(
                datetime.now(UTC) - timedelta(hours=2, minutes=1)
            )
        )

        assert "vor 2 Stunden" in html
