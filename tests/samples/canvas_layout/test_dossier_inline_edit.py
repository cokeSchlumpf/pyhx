import pytest
from fastapi.testclient import TestClient

from samples.canvas_layout import extracted_values
from samples.canvas_layout.main import app

KEY = extracted_values.DOSSIER


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(extracted_values.STORE, KEY, extracted_values._Dossier())
    return TestClient(app)


def _value(html: str, item_id: str) -> str:
    start = html.index(f'id="{item_id}"')
    marker = '<span class="hx-inline-edit__value">'
    begin = html.index(marker, start) + len(marker)
    return html[begin : html.index("</span>", begin)]


class TestDossierInlineEdit:
    def test_extracted_values_are_editable(self, client):
        html = client.get("/dossier").text
        assert 'data-hx-inline-edit-group="extracted"' in html
        for label in ("Tätigkeit", "Pensum", "Beginn AU", "Grad AU"):
            assert f'aria-label="Bearbeiten: {label}"' in html
        assert _value(html, extracted_values.workload.item_id(KEY)) == "100%"
        assert (
            _value(html, extracted_values.incapacity_start.item_id(KEY)) == "20.01.2026"
        )

    def test_aside_has_a_reading_with_hint(self, client):
        html = client.get("/dossier").text
        assert 'data-hx-inline-edit-group="review"' in html
        assert '<span class="hx-inline-edit__hint">unsicher gelesen</span>' in html
        assert (
            _value(html, extracted_values.reading.item_id(KEY))
            == "100% seit 28.04.2026"
        )

    def test_save_updates_store_and_page(self, client):
        url = extracted_values.workload.form.submit_form_fragment.url()
        response = client.post(url, params={"key": KEY}, data={"value": "80"})
        assert '<span class="hx-inline-edit__value">80%</span>' in response.text
        assert "Korrigiert" in response.text
        assert extracted_values.STORE[KEY].workload == 80
        html = client.get("/dossier").text
        assert _value(html, extracted_values.workload.item_id(KEY)) == "80%"

    def test_invalid_value_is_shown_in_german(self, client):
        url = extracted_values.workload.form.submit_form_fragment.url()
        response = client.post(url, params={"key": KEY}, data={"value": "120"})
        assert "Zwischen 0 und 100 %" in response.text
        assert extracted_values.STORE[KEY].workload == 100

    def test_future_date_is_rejected(self, client):
        url = extracted_values.incapacity_start.form.submit_form_fragment.url()
        response = client.post(url, params={"key": KEY}, data={"value": "2999-01-01"})
        assert "Darf nicht in der Zukunft liegen" in response.text

    def test_correcting_the_reading_removes_the_hint(self, client):
        url = extracted_values.reading.form.submit_form_fragment.url()
        response = client.post(
            url, params={"key": KEY}, data={"degree": "80", "since": "2026-04-28"}
        )
        assert "80% seit 28.04.2026" in response.text
        assert "unsicher gelesen" not in response.text
