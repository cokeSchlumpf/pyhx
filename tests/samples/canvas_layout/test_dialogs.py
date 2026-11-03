import re

from fastapi.testclient import TestClient

from samples.canvas_layout import dialogs
from samples.canvas_layout.main import app

HTMX = {"HX-Request": "true"}


def _client() -> TestClient:
    return TestClient(app)


class TestDialogsPage:
    def test_page_opens_no_dialog_and_offers_three(self):
        html = _client().get("/dialogs").text

        assert 'data-hx-design="canvas"' in html
        assert '<div class="hx-dialog">' in html
        assert "aria-modal" not in html
        assert html.count(">Show dialog</button>") == 3
        assert f'hx-get="{dialogs.show_notice.url()}"' in html

    def test_overview_links_to_the_dialogs_page(self):
        assert 'href="/dialogs"' in _client().get("/").text


class TestRequiredNotice:
    def test_notice_is_required(self):
        html = _client().get(dialogs.show_notice.url(), headers=HTMX).text

        assert '<dialog id="dialog-content" open aria-modal="true"' in html
        assert "Demo instance" in html
        assert "data-hx-dialog-close" not in html
        assert 'name="dont_show_again"' in html

    def test_missing_confirmation_returns_the_dialog_with_an_error(self):
        html = _client().post(dialogs.accept_notice.url(), headers=HTMX, data={}).text

        assert " open " in html
        assert 'aria-invalid="true"' in html
        assert "Confirm this to continue." in html

    def test_accepting_closes_the_dialog_and_echoes_the_choice(self):
        html = (
            _client()
            .post(
                dialogs.accept_notice.url(),
                headers=HTMX,
                data={"accepted": "true", "dont_show_again": "true"},
            )
            .text
        )

        assert html.startswith('<dialog id="dialog-content" tabindex="-1"')
        assert "aria-modal" not in html
        assert "be shown again." in html
        assert "will be shown again" not in html


class TestConfirmation:
    def test_cancel_closes_through_close_dialog_and_is_focused(self):
        html = _client().get(dialogs.show_confirm.url(), headers=HTMX).text

        assert "data-hx-dialog-close" in html
        cancel = re.search(r"<button[^>]*>Cancel</button>", html)
        assert cancel is not None
        assert "autofocus" in cancel.group(0)
        assert 'hx-post="/_components/close_dialog/close"' in cancel.group(0)

    def test_close_dialog_closes_it(self):
        html = _client().post("/_components/close_dialog/close", headers=HTMX, data={"id": "dialog-content"}).text

        assert "aria-modal" not in html


class TestDrawerAboveTheDialog:
    def test_dialog_contains_a_drawer_select_that_opens_the_popup_drawer(self):
        html = _client().get(dialogs.show_hand_over.url(), headers=HTMX).text

        assert " open " in html
        assert "hx-drawer-select" in html
        assert "#drawer-content-popup" in html

    def test_hand_over_echoes_the_chosen_owners(self):
        html = (
            _client()
            .post(dialogs.hand_over.url(), headers=HTMX, data={"owner": ["anna", "lena"]})
            .text
        )

        assert "Handed over to Anna Schmidt, Lena Fischer." in html
        assert "aria-modal" not in html
