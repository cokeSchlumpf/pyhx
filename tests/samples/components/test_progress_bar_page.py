import pytest
from fastapi.testclient import TestClient

from samples.canvas_layout.main import app as canvas_app
from samples.components.main import app as components_app


@pytest.mark.parametrize(
    ("app", "path"),
    [(components_app, "/progress-bar"), (canvas_app, "/progress-bars")],
)
def test_the_page_shows_every_mode_with_code(app, path: str) -> None:
    html = TestClient(app).get(path).text

    assert "hx-progress-bar--waiting" in html
    for motion in ("sheen", "stripes", "pulse"):
        assert f"hx-progress-bar--{motion}" in html
    for appearance in ("primary", "info", "neutral", "success", "warning", "danger"):
        assert f"hx-progress-bar--{appearance}" in html
    assert "hx-code" in html
    assert "docs:start" not in html


@pytest.mark.parametrize(
    ("app", "link"),
    [(components_app, 'href="/progress-bar"'), (canvas_app, 'href="/progress-bars"')],
)
def test_the_home_page_links_it(app, link: str) -> None:
    assert link in TestClient(app).get("/").text
