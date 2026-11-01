from fastapi.testclient import TestClient

from samples.canvas_layout.main import app


class TestFormsPage:
    def test_renders_case_form_states_and_aside_in_canvas_design(self):
        response = TestClient(app).get("/forms")

        assert response.status_code == 200
        html = response.text
        assert 'data-hx-design="canvas"' in html
        assert 'id="hx-data-form__case"' in html
        assert 'aria-invalid="true"' in html
        assert 'aria-invalid="false"' in html
        assert "readonly" in html
        assert "disabled" in html
        assert 'role="switch"' in html
        assert "Korrektur speichern" in html

    def test_overview_links_to_forms_page(self):
        response = TestClient(app).get("/")

        assert 'href="/forms"' in response.text
