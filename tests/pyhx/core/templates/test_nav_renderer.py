import asyncio
from types import SimpleNamespace
from typing import cast

import htpy as y
from htpy import li, span

from pyhx.core.request_context import RequestContext
from pyhx.core.templates.nav import AppNavFn, Nav, NavItem
from pyhx.core.templates.nav_renderer import NavRenderer


def _ctx(path: str = "/") -> RequestContext:
    return cast(
        RequestContext,
        SimpleNamespace(request=SimpleNamespace(url=SimpleNamespace(path=path))),
    )


def _slot(nav: Nav) -> AppNavFn:
    async def fn(ctx: RequestContext) -> Nav:
        return nav

    return {"main": fn}


def _render_node(renderer: NavRenderer, nav: AppNavFn, path: str = "/") -> y.Node:
    return asyncio.run(renderer(slot="main", ctx=_ctx(path), navigation=nav))


def _render(renderer: NavRenderer, nav: AppNavFn, path: str = "/") -> str:
    return str(_render_node(renderer, nav, path))


class TestFlat:

    def test_renders_flat_list_as_nav_ul_li(self):
        nav = _slot([NavItem("Home", "/"), NavItem("About", "/about")])
        html = _render(NavRenderer(), nav, path="/elsewhere")
        assert html == (
            "<nav><ul>"
            '<li><a href="/">Home</a></li>'
            '<li><a href="/about">About</a></li>'
            "</ul></nav>"
        )

    def test_marks_active_item(self):
        nav = _slot([NavItem("Home", "/"), NavItem("About", "/about")])
        html = _render(NavRenderer(), nav, path="/about")
        assert '<a href="/about" class="active">About</a>' in html
        assert '<a href="/">Home</a>' in html

    def test_passes_in_group_false_for_flat(self):
        seen: list[bool] = []

        class R(NavRenderer):
            def render_item(self, *, item, is_active, in_group):
                seen.append(in_group)
                return super().render_item(
                    item=item, is_active=is_active, in_group=in_group
                )

        _render(R(), _slot([NavItem("Home", "/")]))
        assert seen == [False]


class TestGrouped:

    def test_renders_groups_with_labels(self):
        nav = _slot(
            {
                "Main": [NavItem("Home", "/")],
                "Admin": [NavItem("Users", "/admin/users")],
            }
        )
        html = _render(NavRenderer(), nav, path="/elsewhere")
        assert html == (
            "<nav>"
            '<div><h3>Main</h3><ul><li><a href="/">Home</a></li></ul></div>'
            "<div><h3>Admin</h3>"
            '<ul><li><a href="/admin/users">Users</a></li></ul></div>'
            "</nav>"
        )

    def test_passes_in_group_true_for_grouped(self):
        seen: list[bool] = []

        class R(NavRenderer):
            def render_item(self, *, item, is_active, in_group):
                seen.append(in_group)
                return super().render_item(
                    item=item, is_active=is_active, in_group=in_group
                )

        nav = _slot({"Main": [NavItem("Home", "/"), NavItem("About", "/about")]})
        _render(R(), nav)
        assert seen == [True, True]

    def test_marks_active_inside_group(self):
        nav = _slot({"Main": [NavItem("Home", "/"), NavItem("About", "/about")]})
        html = _render(NavRenderer(), nav, path="/about")
        assert '<a href="/about" class="active">About</a>' in html


class TestMissingSlot:

    def test_calls_render_empty_when_slot_missing(self):
        seen: list[str] = []

        class R(NavRenderer):
            def render_empty(self, *, slot):
                seen.append(slot)
                return super().render_empty(slot=slot)

        node = asyncio.run(
            R()(slot="missing", ctx=_ctx(), navigation={})
        )
        assert seen == ["missing"]
        assert str(node) == ""


class TestCustomization:

    def test_subclass_overriding_only_render_item_still_orchestrates(self):
        class R(NavRenderer):
            def render_item(self, *, item, is_active, in_group):
                return li[span[item.label]]

        html = _render(R(), _slot([NavItem("Home", "/")]))
        assert html == "<nav><ul><li><span>Home</span></li></ul></nav>"

    def test_render_root_receives_uniform_sections(self):
        seen: list[int] = []

        class R(NavRenderer):
            def render_root(self, *, slot, sections):
                seen.append(len(sections))
                return super().render_root(slot=slot, sections=sections)

        _render(R(), _slot([NavItem("Home", "/")]))
        _render(
            R(), _slot({"A": [NavItem("Home", "/")], "B": [NavItem("X", "/x")]})
        )
        assert seen == [1, 2]
