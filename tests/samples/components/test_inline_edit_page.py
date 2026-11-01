from fastapi.testclient import TestClient

from samples.components.main import app


def test_inline_edit_page_renders_editable_values():
    html = TestClient(app).get("/inline-edit").text
    assert 'data-hx-inline-edit-group="project"' in html
    for label in ("Owner", "Budget", "Due date"):
        assert f'aria-label="Edit {label}"' in html
    assert '<span class="hx-inline-edit__value">120 kCHF</span>' in html


def test_inline_edit_page_is_linked_from_home():
    assert 'href="/inline-edit"' in TestClient(app).get("/").text
