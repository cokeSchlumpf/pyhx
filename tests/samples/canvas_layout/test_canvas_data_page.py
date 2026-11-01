import asyncio

from fastapi.testclient import TestClient

from samples.canvas_layout import data_page
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

    def test_edit_drawer_has_footer_slots(self):
        # A row click renders the edit drawer: the form, cancel and the delete
        # action in the slots the canvas design lays out as a fixed footer.
        case = data_page._cases()[0]

        async def render() -> str:
            # _on_select hands back the drawer's coroutine, as htmx rendering
            # awaits nodes.
            return str(await (await data_page.cases.section._on_select([case])))  # type: ignore[misc]

        html = asyncio.run(render())

        assert '<div class="hx-data-form-drawer">' in html
        assert 'class="hx-data-form-drawer__cancel"' in html
        assert 'class="hx-data-form-drawer__delete"' in html
        assert "Fall löschen" in html
