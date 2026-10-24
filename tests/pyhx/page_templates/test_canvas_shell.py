import htpy as y
import pytest
from fastapi.testclient import TestClient

from pyhx.components import DRAWER_CONTENT_ID, POPUP_DRAWER_CONTENT_ID
from pyhx.core import PageResponse, RequestContext, WebApp
from pyhx.page_templates import AppShell, CanvasShell


def _get(page_template, path: str = "/") -> str:
    hx = WebApp(title="App", default_page_template=page_template)

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.p(id="body")["content"]

    @hx.page("/full", title="Full")
    async def full() -> PageResponse:
        return PageResponse(node=y.p["full"], page_template=CanvasShell(mode="full"))

    return TestClient(hx.create_app()).get(path).text


class TestCanvasShell:
    def test_design_is_canvas(self):
        assert CanvasShell().design == "canvas"
        assert 'data-hx-design="canvas"' in _get(CanvasShell())

    def test_renders_page_template_and_default_mode(self):
        html = _get(CanvasShell())
        assert (
            '<body data-hx-page-template="canvas-shell" data-hx-mode="centered">'
            in html
        )

    @pytest.mark.parametrize("mode", ["centered", "wide", "full"])
    def test_renders_mode(self, mode):
        assert f'data-hx-mode="{mode}"' in _get(CanvasShell(mode=mode))

    def test_mode_can_change_per_page(self):
        assert 'data-hx-mode="full"' in _get(CanvasShell(), "/full")

    def test_renders_body_in_content_area(self):
        html = _get(CanvasShell())
        assert (
            '<div class="hx-canvas-shell__content"><p id="body">content</p></div>'
            in html
        )

    def test_loads_theme_after_pyhx_and_before_template_css(self):
        html = _get(CanvasShell())
        positions = [
            html.index(href)
            for href in (
                "/static/css/pyhx.css",
                "/static/css/themes/canvas.css",
                "/static/css/page-templates/canvas-shell.css",
            )
        ]
        assert positions == sorted(positions)

    def test_uses_pyhx_mark_as_logo_and_favicon(self):
        html = _get(CanvasShell())
        assert '<img src="/static/images/pyhx_mark.svg"' in html
        assert (
            '<link rel="icon" type="image/svg+xml" href="/static/images/pyhx_mark.svg">'
            in html
        )

    def test_favicon_can_be_replaced(self):
        assert 'href="/static/images/custom.svg"' in _get(
            CanvasShell(favicon="/static/images/custom.svg")
        )

    def test_brand_falls_back_to_app_title(self):
        assert '<span class="hx-brand__title">App</span>' in _get(CanvasShell())

    def test_static_header_content_keeps_attributes(self):
        html = _get(CanvasShell(header_content=y.span(class_="org")["Muster AG"]))
        assert '<span class="org">Muster AG</span>' in html

    def test_header_content_is_evaluated_per_request(self):
        def header_content() -> y.Node:
            return RequestContext.get().user.display_name

        assert "Anonymous User" in _get(CanvasShell(header_content=header_content))

    def test_async_header_content(self):
        async def header_content() -> y.Node:
            return y.span["async"]

        assert "<span>async</span>" in _get(CanvasShell(header_content=header_content))

    def test_mounts_drawers_notifications_and_error_toasts(self):
        html = _get(CanvasShell())
        assert f'id="{DRAWER_CONTENT_ID}"' in html
        assert f'id="{POPUP_DRAWER_CONTENT_ID}"' in html
        assert 'id="hx-notifications"' in html
        assert 'id="hx-notification__error-template"' in html
        assert "/static/js/pyhx.notifications.js" in html


class TestAppShellErrorToasts:
    def test_app_shell_still_loads_error_toasts(self):
        html = _get(AppShell())
        assert "/static/js/pyhx.app-shell.js" in html
        assert "/static/js/pyhx.notifications.js" in html
        assert 'id="hx-notification__error-template"' in html
