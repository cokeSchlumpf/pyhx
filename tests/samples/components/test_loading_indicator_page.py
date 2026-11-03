import pytest
from fastapi.testclient import TestClient

from samples.canvas_layout.main import app as canvas_app
from samples.components.main import app as components_app


@pytest.mark.parametrize(
    ("app", "path"),
    [(components_app, "/loading-indicator"), (canvas_app, "/loading-indicators")],
)
def test_the_page_shows_every_variant_and_use_with_code(app, path: str) -> None:
    html = TestClient(app).get(path).text

    for kind in ("spinner", "ripple", "pulse", "dots", "bars"):
        assert f"hx-loading-indicator--{kind}" in html
    for appearance in ("primary", "info", "neutral", "success", "warning", "danger"):
        assert f"hx-loading-indicator--{appearance}" in html
    for size in ("sm", "md", "lg"):
        assert f"hx-loading-indicator--{size}" in html
    assert "hx-pill__label" in html
    assert "hx-button--solid" in html
    assert "<table>" in html
    assert 'aria-label="Sections"' in html
    assert "hx-code" in html
    assert "docs:start" not in html


@pytest.mark.parametrize(
    ("app", "link"),
    [
        (components_app, 'href="/loading-indicator"'),
        (canvas_app, 'href="/loading-indicators"'),
    ],
)
def test_the_home_page_links_it(app, link: str) -> None:
    assert link in TestClient(app).get("/").text
