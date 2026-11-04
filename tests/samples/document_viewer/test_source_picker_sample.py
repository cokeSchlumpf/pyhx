from fastapi.testclient import TestClient

from samples.document_viewer.main import app


class TestSourcePickerSample:
    def test_the_overview_links_the_example(self):
        assert 'href="/source-picker"' in TestClient(app).get("/").text

    def test_the_page_shows_code_and_a_button_for_the_dialog(self):
        html = TestClient(app).get("/source-picker").text

        assert "hx-code" in html
        assert "docs:start" not in html
        assert 'hx-get="/source-picker/dialog"' in html
        assert "Nothing chosen yet." in html

    def test_the_dialog_holds_a_picker(self):
        html = TestClient(app).get("/source-picker/dialog", headers={"HX-Request": "true"}).text

        assert 'data-hx-source-picker="source"' in html
        assert 'name="source_document" value="anmeldung"' in html

    def test_editing_opens_at_the_source(self):
        html = TestClient(app).get(
            "/source-picker/dialog?document=arztbericht&page=2&box=0.1,0.1,0.5,0.2",
            headers={"HX-Request": "true"},
        ).text

        assert 'data-hx-document-start="arztbericht:2"' in html
        assert 'name="source_box" value="0.1000,0.1000,0.5000,0.2000"' in html

    def test_a_single_document_has_its_title_and_no_switcher(self):
        html = TestClient(app).get("/source-picker/single", headers={"HX-Request": "true"}).text

        assert "hx-document-viewer__title" in html
        assert "hx-document-viewer__files" not in html
        assert 'name="source_document" value="arztbericht"' in html

    def test_many_documents_have_the_switcher(self):
        html = TestClient(app).get("/source-picker/many", headers={"HX-Request": "true"}).text

        assert "1 of 30 documents" in html
        assert 'href="/source-picker/many/picker?document=cor-07"' in html
        assert html.count("data-hx-document-page=") == 12  # only the current document

    def test_a_switcher_entry_returns_the_picker_for_its_document(self):
        html = TestClient(app).get(
            "/source-picker/many/picker?document=cor-07", headers={"HX-Request": "true"}
        ).text

        assert 'id="source-picker"' in html
        assert 'name="source_document" value="cor-07"' in html
        assert 'name="source_page" value="1"' in html
        assert "<dialog" not in html

    def test_posting_closes_the_dialog_and_echoes_the_choice(self):
        html = TestClient(app).post(
            "/source-picker/use",
            data={"source_document": "arztbericht", "source_page": "2", "source_box": "0.1,0.1,0.5,0.2"},
            headers={"HX-Request": "true"},
        ).text

        assert 'id="source-picker-result"' in html
        assert "page 2" in html
        assert "the area 0.1000,0.1000,0.5000,0.2000" in html
