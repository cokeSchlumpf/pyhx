from fastapi.testclient import TestClient

from samples.components.main import app
from samples.components.pages import dialog

HTMX = {"HX-Request": "true"}


class TestDialogPage:
    def test_page_shows_both_examples_with_their_code_and_no_open_dialog(self):
        html = TestClient(app).get("/dialog").text

        assert 'data-hx-design="default"' in html
        assert html.count(">Show dialog</button>") == 2
        assert "closable=False" in html
        assert "aria-modal" not in html

    def test_home_and_navigation_link_to_the_page(self):
        html = TestClient(app).get("/").text

        assert html.count('href="/dialog"') >= 2

    def test_notice_error_and_accept(self):
        client = TestClient(app)

        refused = client.post(dialog.accept.url(), headers=HTMX, data={}).text
        accepted = client.post(
            dialog.accept.url(), headers=HTMX, data={"accepted": "true"}
        ).text

        assert "Confirm this to continue." in refused
        assert "show again: no)." in accepted
        assert "aria-modal" not in accepted

    def test_confirmation_opens(self):
        html = TestClient(app).get(dialog.show_confirm.url(), headers=HTMX).text

        assert "Delete project?" in html
        assert "data-hx-dialog-close" in html
