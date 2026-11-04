"""The Timeline page of the components sample and its drawer route."""

import re

from fastapi.testclient import TestClient

from samples.components.main import app
from samples.components.pages.timeline import SAMPLE


def _client() -> TestClient:
    return TestClient(app)


def test_the_page_shows_the_timeline_with_code() -> None:
    html = _client().get("/timeline").text

    assert 'id="product-year"' in html
    assert 'data-timeline-open-url="/timeline/events"' in html
    assert "hx-code" in html
    assert "docs:start" not in html
    assert "/static/js/pyhx.timeline.js" in html


def test_the_page_reads_its_state_from_the_url() -> None:
    html = _client().get("/timeline?types=sprint&from=2026-03-01&to=2026-04-15").text

    assert re.search(r'aria-pressed="true" data-timeline-category="sprint"', html)
    assert re.search(r'aria-pressed="false" data-timeline-category="release"', html)
    # 2026-03-01 and 2026-04-15 as days since 1970-01-01.
    assert 'name="product-year-span" value="20513"' in html
    assert 'name="product-year-span" value="20558"' in html


def test_the_drawer_shows_one_event() -> None:
    event = SAMPLE[0].event
    html = _client().get(f"/timeline/events?key={event.key}").text

    assert 'id="drawer-content"' in html
    assert "Sprint 1" in html
    assert "Next event" not in html


def test_the_drawer_pages_through_combined_events() -> None:
    keys = [s.event.key for s in SAMPLE if s.event.category == "incident"][:3]
    query = "&".join(f"key={k}" for k in keys)

    first = _client().get(f"/timeline/events?{query}").text
    second = _client().get(f"/timeline/events?{query}&index=1").text

    assert "3 events" in first
    assert "1 / 3" in first
    assert "2 / 3" in second
    assert "Slow search" in first
    assert "Outage of the API" in second
    assert "Flagged" in second


def test_the_drawer_without_known_events() -> None:
    html = _client().get("/timeline/events?key=nope").text

    assert "exist anymore" in html


def test_the_home_page_links_it() -> None:
    assert 'href="/timeline"' in _client().get("/").text
