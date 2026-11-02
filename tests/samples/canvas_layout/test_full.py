from fastapi.testclient import TestClient

from samples.canvas_layout.main import app


class TestFullPage:
    def test_shows_a_document_viewer_filling_the_window(self):
        html = TestClient(app).get("/full").text

        assert 'data-hx-document-viewer="full"' in html
        assert 'class="hx-document-viewer__thumbnails"' in html
        assert 'class="hx-document-viewer__sidebar"' in html
        assert 'data-hx-document-annotation="full:beruf"' in html
        assert 'href="/dossier"' in html

    def test_serves_its_page_images(self):
        assert TestClient(app).get("/sample-pages/anmeldung/1.svg").status_code == 200
