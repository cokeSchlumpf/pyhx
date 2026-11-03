import re

import htpy as y
import pytest
from fastapi.testclient import TestClient

import pyhx.components as c
from pyhx.core import RequestContext, WebApp
from pyhx.page_templates import AppShell, CanvasShell

TEMPLATES = [CanvasShell, AppShell]


def _get(page_template) -> str:
    hx = WebApp(title="App", default_page_template=page_template)

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.p["content"]

    return TestClient(hx.create_app()).get("/").text


def _notice() -> y.Node:
    return c.dialog_content(y.p["Use only test data."], title="Demo instance", closable=False)


@pytest.mark.parametrize("template", TEMPLATES)
class TestDialogInTemplates:
    def test_mount_is_rendered_empty_by_default(self, template):
        html = _get(template())

        assert '<div class="hx-dialog">' in html
        assert re.search(r'<dialog id="dialog-content" tabindex="-1"[^>]*></dialog>', html)

    def test_mount_comes_after_the_drawers(self, template):
        html = _get(template())

        assert html.index('id="drawer-content-popup"') < html.index('<div class="hx-dialog">')
        assert html.index('<div class="hx-dialog">') < html.index('id="hx-notifications"')

    def test_page_is_delivered_with_the_dialog_open(self, template):
        html = _get(template(dialog_content=_notice))

        assert '<dialog id="dialog-content" open aria-modal="true"' in html
        assert "Use only test data." in html
        assert "data-hx-dialog-close" not in html

    def test_async_producer_reads_the_request(self, template):
        async def notice() -> y.Node | None:
            return _notice() if RequestContext.get_request().url.path == "/" else None

        assert " open " in _get(template(dialog_content=notice))

    def test_producer_returning_none_renders_the_closed_mount(self, template):
        html = _get(template(dialog_content=lambda: None))

        assert '<div class="hx-dialog">' in html
        assert "aria-modal" not in html
