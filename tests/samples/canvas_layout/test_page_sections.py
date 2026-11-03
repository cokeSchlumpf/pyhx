from pathlib import Path

from fastapi.testclient import TestClient

from samples.canvas_layout.main import app

CSS = Path(__file__).resolve().parents[3] / "src" / "pyhx" / "static" / "css"


class TestCanvasPageSections:
    def test_page_renders_a_header_and_one_section_per_table(self):
        response = TestClient(app).get("/page-sections")

        assert response.status_code == 200
        assert 'data-hx-design="canvas"' in response.text
        assert response.text.count('class="hx-page-section"') == 2
        assert "Offene Fälle" in response.text and "Abgeschlossene Fälle" in response.text
        assert "IV-2026-0142" in response.text and "IV-2025-0988" in response.text

    def test_overview_links_the_page(self):
        assert 'href="/page-sections"' in TestClient(app).get("/").text

    def test_a_table_in_a_section_is_a_card_like_the_table_of_a_data_page(self):
        shell = (CSS / "page-templates" / "canvas-shell.css").read_text()
        section = (CSS / "pyhx" / "components" / "layout" / "page-section.css").read_text()

        assert ".hx-page-section__content > .hx-table__wrapper {" in shell
        assert '[data-hx-design="canvas"] .hx-page-section__header {' in section
