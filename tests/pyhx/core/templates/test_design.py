from contextvars import Context

import htpy as y
from fastapi.testclient import TestClient

from pyhx.core import PageResponse, RequestContext, WebApp, hx
from pyhx.core.primitives import omit
from pyhx.core.request_context import set_request_context
from pyhx.core.templates import Skeleton
from pyhx.page_templates import AppShell


class _NoDesignTemplate:
    """A template satisfying ``PageTemplate`` only by its call signature."""

    async def __call__(self, *, request, app_title, page_title, body, navigation):
        return body


def _build_app(page_template=None) -> WebApp:
    hx = WebApp(default_page_template=page_template)

    @hx.fragment.get("/design")
    async def design_fragment() -> y.Node:
        return y.span[RequestContext.get_design()]

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.span(id="design")[RequestContext.get_design()]

    return hx


class TestTemplateDesign:
    def test_skeleton_is_plain(self):
        assert Skeleton().design == "plain"

    def test_skeleton_takes_design_from_wrapping_template(self):
        assert Skeleton(design="canvas").design == "canvas"

    def test_app_shell_is_default(self):
        assert AppShell().design == "default"


class TestGetDesign:
    def test_plain_outside_a_request(self):
        assert Context().run(RequestContext.get_design) == "plain"

    def test_plain_without_page_template(self):
        def _check() -> str:
            set_request_context(RequestContext())
            return RequestContext.get_design()

        assert Context().run(_check) == "plain"

    def test_plain_for_template_without_design_attribute(self):
        def _check() -> str:
            set_request_context(RequestContext(page_template=_NoDesignTemplate()))
            return RequestContext.get_design()

        assert Context().run(_check) == "plain"

    def test_reads_design_of_page_template_in_context(self):
        def _check() -> str:
            set_request_context(RequestContext(page_template=AppShell()))
            return RequestContext.get_design()

        assert Context().run(_check) == "default"

    def test_fragment_sees_default_page_template_design(self):
        client = TestClient(_build_app(Skeleton(design="canvas")).create_app())
        assert client.get("/design").text == "<span>canvas</span>"

    def test_fragment_without_configured_template_is_plain(self):
        client = TestClient(_build_app().create_app())
        assert client.get("/design").text == "<span>plain</span>"

    def test_page_body_sees_default_page_template_design(self):
        client = TestClient(_build_app(Skeleton(design="canvas")).create_app())
        assert '<span id="design">canvas</span>' in client.get("/").text


class TestWebAppDesign:
    def test_reads_default_page_template_design(self):
        assert WebApp(default_page_template=AppShell()).design == "default"

    def test_plain_without_configured_template(self):
        assert WebApp().design == "plain"

    def test_hx_design_in_request(self):
        app = WebApp(default_page_template=Skeleton(design="canvas"))

        @app.fragment.get("/hx-design")
        async def hx_design() -> y.Node:
            return y.span[hx.design]

        client = TestClient(app.create_app())
        assert client.get("/hx-design").text == "<span>canvas</span>"


class TestDesignAttribute:
    def test_page_renders_design_on_html_element(self):
        client = TestClient(_build_app(Skeleton(design="canvas")).create_app())
        assert (
            '<html data-theme="light" data-hx-design="canvas">' in client.get("/").text
        )

    def test_plain_skeleton_renders_plain(self):
        client = TestClient(_build_app().create_app())
        assert 'data-hx-design="plain"' in client.get("/").text


class TestPageTemplateOmit:
    def test_omit_skips_the_page_template(self):
        hx = WebApp()

        @hx.page("/raw", title="Raw")
        async def raw() -> PageResponse:
            return PageResponse(node=y.p["body only"], page_template=omit)

        assert TestClient(hx.create_app()).get("/raw").text == "<p>body only</p>"

    def test_omit_drops_the_page_title(self):
        hx = WebApp(title="App")

        @hx.page("/untitled", title="Page")
        async def untitled() -> PageResponse:
            return PageResponse(node=y.p["body"], page_title=omit)

        assert "<title>App</title>" in TestClient(hx.create_app()).get("/untitled").text
