"""Errors the app doesn't handle, and HTTP errors, in the language of the request (T-020)."""

import htpy as y
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from pyhx.components.layouts.notifications import notification_error_template
from pyhx.core.primitives.negotiate_locale import LocaleSettings
from pyhx.core.webapp import WebApp
from pyhx.i18n import _catalogs, use_locale

BROWSER = {"Accept": "text/html,application/xhtml+xml", "Accept-Language": "de"}
HTMX = {"HX-Request": "true", "Accept": "*/*", "Accept-Language": "de"}


@pytest.fixture(autouse=True)
def locale_settings(monkeypatch):
    settings = LocaleSettings(
        supported_locales=["en", "de", "it", "fr"], default_locale="en"
    )
    monkeypatch.setattr(LocaleSettings, "read", staticmethod(lambda: settings))
    _catalogs.clear_cache()
    yield
    _catalogs.clear_cache()


class Layout:
    """A page template that marks its output, to see that error pages are inside it."""

    design = "plain"

    def __init__(self, fails: bool = False) -> None:
        self.fails = fails

    async def __call__(self, *, request, app_title, page_title, body, navigation):
        if self.fails:
            raise RuntimeError("the layout failed too")
        return y.html[y.title[page_title], y.main(id="layout")[body]]


def make_app(*, is_dev: bool = False, layout: Layout | None = None) -> WebApp:
    hx = WebApp(is_dev=is_dev, default_page_template=layout or Layout())

    @hx.page("/broken", title="Broken")
    async def broken() -> y.Node:
        raise RuntimeError("secret detail")

    @hx.page("/missing", title="Missing")
    async def missing() -> y.Node:
        raise HTTPException(status_code=404)

    @hx.page("/gone", title="Gone")
    async def gone() -> y.Node:
        raise HTTPException(status_code=404, detail="This case was closed.")

    @hx.fragment.get("/_fragments/broken")
    async def broken_fragment() -> y.Node:
        raise RuntimeError("secret detail")

    @hx.api.get("/api/broken")
    async def broken_api():
        raise RuntimeError("secret detail")

    return hx


def client(hx: WebApp, app: FastAPI | None = None) -> TestClient:
    return TestClient(hx.create_app(app=app), raise_server_exceptions=False)


class TestUnhandledErrors:
    def test_a_page_answers_a_translated_error_page_in_the_layout(self):
        resp = client(make_app()).get("/broken", headers=BROWSER)
        assert resp.status_code == 500
        assert 'id="layout"' in resp.text
        assert "Etwas ist schiefgelaufen" in resp.text
        assert "secret detail" not in resp.text
        assert "Traceback" not in resp.text

    def test_the_trace_is_shown_in_development(self):
        resp = client(make_app(is_dev=True)).get("/broken", headers=BROWSER)
        assert resp.status_code == 500
        assert "secret detail" in resp.text

    def test_the_message_alone_when_the_layout_fails_too(self):
        resp = client(make_app(layout=Layout(fails=True))).get(
            "/broken", headers=BROWSER
        )
        assert resp.status_code == 500
        assert 'id="layout"' not in resp.text
        assert "Etwas ist schiefgelaufen" in resp.text

    @pytest.mark.parametrize("path", ["/_fragments/broken", "/api/broken"])
    def test_fragments_and_endpoints_answer_a_translated_text(self, path):
        resp = client(make_app()).get(path, headers=HTMX)
        assert resp.status_code == 500
        assert resp.headers["content-type"].startswith("text/plain")
        assert "secret detail" not in resp.text
        with use_locale("de"):
            from pyhx.core._errors import error_texts

            assert resp.text == error_texts(500)[1]

    def test_fragments_add_the_trace_in_development(self):
        resp = client(make_app(is_dev=True)).get("/_fragments/broken", headers=HTMX)
        assert "secret detail" in resp.text


class TestHttpErrors:
    def test_an_unknown_url_answers_a_translated_404_page_to_browsers(self):
        resp = client(make_app()).get("/nowhere", headers=BROWSER)
        assert resp.status_code == 404
        assert 'id="layout"' in resp.text
        assert "Seite nicht gefunden" in resp.text

    def test_a_404_raised_by_a_page_answers_the_error_page(self):
        resp = client(make_app()).get("/missing", headers=BROWSER)
        assert resp.status_code == 404
        assert "Seite nicht gefunden" in resp.text

    def test_a_detail_set_by_the_app_is_shown(self):
        resp = client(make_app()).get("/gone", headers=BROWSER)
        assert "This case was closed." in resp.text

    def test_htmx_gets_the_translated_text(self):
        resp = client(make_app()).get("/nowhere", headers=HTMX)
        assert resp.status_code == 404
        assert resp.headers["content-type"].startswith("text/plain")
        assert "Diese Seite existiert nicht" in resp.text

    def test_a_method_not_allowed_keeps_its_status_and_headers(self):
        resp = client(make_app()).post("/missing", headers=BROWSER)
        assert resp.status_code == 405
        assert "allow" in resp.headers

    def test_api_clients_keep_fastapis_json(self):
        resp = client(make_app()).get(
            "/nowhere", headers={"Accept": "application/json"}
        )
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Not Found"}

    def test_a_handler_of_the_app_wins(self):
        hx = make_app()

        async def own(request: Request, exc: Exception) -> PlainTextResponse:
            return PlainTextResponse("own", status_code=418)

        hx.configure_fast_api_app(
            lambda app: app.add_exception_handler(StarletteHTTPException, own)
        )
        assert client(hx).get("/nowhere", headers=BROWSER).text == "own"

    def test_a_handler_passed_to_fastapi_is_kept(self):
        async def own(request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse({"own": True}, status_code=404)

        app = FastAPI(exception_handlers={StarletteHTTPException: own})
        resp = client(make_app(), app).get("/nowhere", headers=BROWSER)
        assert resp.json() == {"own": True}


class TestErrorToast:
    def test_the_template_carries_the_texts_in_the_request_language(self):
        with use_locale("de"):
            html = str(notification_error_template())
        assert 'data-text-request-failed="Anfrage fehlgeschlagen ({status})"' in html
        assert "data-text-connection-lost=" in html
        assert "data-text-timeout=" in html
        assert "data-text-swap-failed=" in html
