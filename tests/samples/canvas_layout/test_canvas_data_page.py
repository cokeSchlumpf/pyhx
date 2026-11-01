from fastapi.testclient import TestClient

from samples.canvas_layout.main import app


class TestCanvasDataPage:
    def test_drawer_page_renders_table_and_create_action(self):
        response = TestClient(app).get("/data-page")

        assert response.status_code == 200
        assert 'data-hx-design="canvas"' in response.text
        assert "IV-2026-0142" in response.text
        assert "Fall erfassen" in response.text

    def test_detail_page_renders_table(self):
        response = TestClient(app).get("/data-page-detail")

        assert response.status_code == 200
        assert "Fälle (Detailseite)" in response.text
        assert "IV-2026-0142" in response.text

    def test_overview_links_both_pages(self):
        response = TestClient(app).get("/")

        assert 'href="/data-page"' in response.text
        assert 'href="/data-page-detail"' in response.text
