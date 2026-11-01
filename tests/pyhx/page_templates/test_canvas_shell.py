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


def _get_with_nav(page_template, path: str = "/") -> str:
    hx = WebApp(title="App", default_page_template=page_template)

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.p(id="body")["content"]

    @hx.page("/users", title="Users")
    async def users() -> y.Node:
        return y.p["users"]

    hx.navigation.set(
        {"": [hx.nav_item(home, full_match=True)], "Admin": [hx.nav_item(users)]}
    )
    hx.navigation.set([hx.nav_item(users, label="Admin users")], slot="admin")

    return TestClient(hx.create_app()).get(path).text


class TestCanvasShellNavigation:
    def test_no_navigation_by_default(self):
        html = _get_with_nav(CanvasShell())
        assert "hx-canvas-nav" not in html
        assert "data-hx-navigation" not in html

    def test_tabs_sit_in_the_header(self):
        html = _get_with_nav(CanvasShell(main_navigation="tabs"))
        assert 'data-hx-navigation="tabs"' in html
        header = html[html.index("<header>") : html.index("</header>")]
        assert '<nav class="hx-canvas-nav" data-hx-placement="tabs"' in header
        assert (
            '<div class="hx-canvas-shell__content"><p id="body">content</p></div>'
            in html
        )

    def test_tab_groups_are_dropdowns(self):
        html = _get_with_nav(CanvasShell(main_navigation="tabs"), "/users")
        assert '<details name="hx-canvas-nav">' in html
        assert '<summary class="active"><span>Admin</span>' in html

    def test_tabs_load_the_dropdown_script(self):
        script = "/static/js/pyhx.canvas-shell.js"
        assert script in _get_with_nav(CanvasShell(main_navigation="tabs"))
        assert script not in _get_with_nav(CanvasShell(main_navigation="sidebar"))
        assert script not in _get_with_nav(CanvasShell())

    def test_sidebar_sits_left_of_the_page(self):
        html = _get_with_nav(CanvasShell(main_navigation="sidebar"))
        assert 'data-hx-navigation="sidebar"' in html
        assert (
            '<div class="hx-canvas-shell__content">'
            '<nav class="hx-canvas-nav" data-hx-placement="sidebar"'
        ) in html
        assert (
            '<div class="hx-canvas-shell__page"><p id="body">content</p></div>' in html
        )
        assert "<h3>Admin</h3>" in html

    def test_marks_the_active_item(self):
        html = _get_with_nav(CanvasShell(main_navigation="sidebar"))
        assert '<a href="/" aria-current="page" class="active">' in html

    def test_navigation_slot(self):
        html = _get_with_nav(
            CanvasShell(main_navigation="sidebar", navigation_slot="admin")
        )
        assert "<span>Admin users</span>" in html
        assert "<h3>Admin</h3>" not in html

    def test_missing_slot_renders_no_navigation(self):
        html = _get_with_nav(
            CanvasShell(main_navigation="sidebar", navigation_slot="missing")
        )
        assert "hx-canvas-nav" not in html
        assert "data-hx-navigation" not in html
        assert (
            '<div class="hx-canvas-shell__content"><p id="body">content</p></div>'
            in html
        )


class TestAppShellErrorToasts:
    def test_app_shell_still_loads_error_toasts(self):
        html = _get(AppShell())
        assert "/static/js/pyhx.app-shell.js" in html
        assert "/static/js/pyhx.notifications.js" in html
        assert 'id="hx-notification__error-template"' in html
