"""The timeline in the canvas design: the page, its drawer route and the link on the home page."""

from fastapi.testclient import TestClient

from samples.canvas_layout.main import app
from samples.canvas_layout.timeline import ENTRIES


def test_the_page_shows_the_timeline_in_a_card() -> None:
    html = TestClient(app).get("/timeline").text

    assert 'data-hx-page-template="canvas-shell"' in html
    assert 'id="dossier-timeline"' in html
    assert 'data-timeline-open-url="/timeline/entries"' in html
    assert "hx-card" in html


def test_the_drawer_pages_through_the_missed_deadlines() -> None:
    keys = [e.event.key for e in ENTRIES if e.event.warn]
    query = "&".join(f"key={k}" for k in keys)

    html = TestClient(app).get(f"/timeline/entries?{query}&index=1").text

    assert "2 entries" in html
    assert "2 / 2" in html
    assert "This deadline was missed." in html


def test_the_home_page_links_it() -> None:
    assert 'href="/timeline"' in TestClient(app).get("/").text
