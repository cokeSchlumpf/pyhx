from collections.abc import Sequence
from typing import Any, Literal, cast

import htpy as y

from ..components.layouts import (
    POPUP_DRAWER_CONTENT_ID,
    drawer,
    notification_error_template,
    notifications,
)
from ..components.primitives import icon
from ..core.primitives import SyncOrAsyncValue, classnames, resolve_value
from ..core.request_context import RequestContext
from ..core.templates.nav import AppNavFn, NavItem
from ..core.templates.nav_renderer import NavRenderer
from ..core.templates.page_template import Design, PageTemplate
from ..core.templates.skeleton import Skeleton
from .settings_menu import DEFAULT_SETTINGS, SettingsEntry, settings_menu

CanvasShellMode = Literal["centered", "wide", "full"]
"""Width of the content area.

- ``centered`` — centered column of at most 72rem (lists, case overviews).
- ``wide`` — centered column of at most ``--hx-container-width-wide``.
- ``full`` — full viewport width without padding (e.g. a document viewer).
"""

CanvasShellNavigation = Literal["tabs", "sidebar"]
"""Placement of the main navigation.

- ``tabs`` — a row of tabs below the top bar, part of the sticky header; for a
  handful of top-level areas. Groups open as a dropdown.
- ``sidebar`` — a column on the canvas, left of the content; for many items
  in labelled groups (e.g. admin pages).
"""


class CanvasShellNavRenderer(NavRenderer):
    """Renders a navigation slot as the tabs or the sidebar of the canvas."""

    def __init__(self, placement: CanvasShellNavigation) -> None:
        self.placement = placement

    def render_item(
        self,
        *,
        item: NavItem,
        is_active: bool,
        in_group: bool,
    ) -> y.Node:
        # Icons only in the sidebar and in tab dropdowns; a tab row reads
        # better as plain words.
        show_icon = self.placement == "sidebar" or in_group
        return y.li[
            y.a(
                href=str(item.to),
                aria_current="page" if is_active else None,
                **classnames({"active": is_active}),
            )[
                icon(item.icon) if item.icon and show_icon else None,
                y.span[item.label],
            ]
        ]

    def render_group(
        self, *, label: str, items: list[y.Node], has_active: bool
    ) -> y.Node:
        if self.placement == "tabs":
            return y.li(class_="hx-canvas-nav__group")[
                y.details(name="hx-canvas-nav")[
                    y.summary(**classnames({"active": has_active}))[
                        y.span[label], icon("chevron-down")
                    ],
                    y.ul[items],
                ]
            ]
        return y.li(class_="hx-canvas-nav__group")[y.h3[label], y.ul[items]]

    def render_flat(self, *, items: list[y.Node]) -> y.Node:
        return items

    def render_root(self, *, slot: str, sections: list[y.Node]) -> y.Node:
        return y.nav(
            class_="hx-canvas-nav",
            data_hx_placement=self.placement,
            aria_label=slot,
        )[y.ul[sections]]

    def render_empty(self, *, slot: str) -> y.Node:
        return None


class CanvasShell(PageTemplate):
    """Page template of the ``canvas`` design: a top bar above a grey canvas.

    The shell renders the top bar (brand on the left, ``header_content`` on
    the right) and the content area; pages place their own breadcrumbs and
    content cards on the canvas. Drawers, notifications and the htmx error
    toasts are mounted like in :class:`AppShell`, so drawer-based components
    (e.g. DataPage forms and filters) keep working.

    ``header_content`` is either a node or a zero-argument producer, sync or
    async, evaluated per request — read request data inside it via
    :class:`RequestContext`::

        def header_content() -> y.Node:
            return RequestContext.get().user.display_name

        CanvasShell(header_content=header_content)

    ``main_navigation`` adds the app's navigation (slot ``navigation_slot``,
    default ``main``) as ``"tabs"`` below the top bar or as a ``"sidebar"``
    left of the content. Without it (the default) the shell has no
    navigation, as before. Set it per page to give only some pages a
    navigation, e.g. the admin pages::

        PageResponse(
            node=...,
            page_template=CanvasShell(
                main_navigation="sidebar", navigation_slot="admin"
            ),
        )

    ``settings`` fills the settings menu, a gear right of ``header_content``
    opening a dropdown with one section per entry. The default is the
    language of the app (:class:`~pyhx.page_templates.LanguageSetting`),
    shown when the app offers several languages; ``settings=()`` removes the
    gear. An entry is any callable returning a section (see
    :class:`~pyhx.page_templates.SettingsEntry`).
    """

    design: Design = "canvas"

    def __init__(
        self,
        *,
        brand_img_alt: str | None = None,
        brand_img_src: str = "/static/images/pyhx_mark.svg",
        favicon: str = "/static/images/pyhx_mark.svg",
        header_content: SyncOrAsyncValue[y.Node] = None,
        main_navigation: CanvasShellNavigation | None = None,
        navigation_slot: str = "main",
        mode: CanvasShellMode = "centered",
        stylesheets: tuple[str, ...] = (),
        settings: Sequence[SettingsEntry] = DEFAULT_SETTINGS,
        scripts: tuple[str, ...] = (),
    ) -> None:
        self.brand_image_alt = brand_img_alt
        self.brand_image_src = brand_img_src
        self.favicon = favicon
        self.header_content = header_content
        self.main_navigation = main_navigation
        self.navigation_slot = navigation_slot
        self.mode = mode
        self.stylesheets = stylesheets
        self.settings = tuple(settings)
        self.scripts = scripts

    async def __call__(
        self,
        *,
        request: RequestContext,
        app_title: str,
        page_title: str | None,
        body: y.Node,
        navigation: AppNavFn,
    ) -> y.Node:
        if self.main_navigation:
            nav: y.Node = await CanvasShellNavRenderer(self.main_navigation)(
                slot=self.navigation_slot, ctx=request, navigation=navigation
            )
        else:
            nav = None

        skeleton = Skeleton(
            design=self.design,
            favicon=self.favicon,
            stylesheets=(
                "/static/css/fonts.css",
                "/static/css/pyhx.css",
                "/static/css/themes/canvas.css",
                "/static/css/page-templates/canvas-shell.css",
                *self.stylesheets,
            ),
            scripts=(
                "/static/js/pyhx.notifications.js",
                *(
                    ("/static/js/pyhx.canvas-shell.js",)
                    if self.main_navigation == "tabs"
                    else ()
                ),
                *self.scripts,
            ),
        )

        return await skeleton(
            request=request,
            app_title=app_title,
            page_title=page_title,
            body=await self._render_page(app_title=app_title, body=body, nav=nav),
            navigation=navigation,
        )

    async def _render_page(
        self, *, app_title: str, body: y.Node, nav: y.Node
    ) -> y.Node:
        title = self.brand_image_alt or app_title
        # `y.Node` itself contains awaitables and iterables, so mypy can't
        # solve `resolve_value`'s type parameter from it; same cast as in
        # DataSection.
        header_content: y.Node = await resolve_value(
            cast(SyncOrAsyncValue[Any], self.header_content)
        )

        # Without a navigation the markup stays exactly as before, so pages
        # built for the plain canvas are unaffected.
        placement = self.main_navigation if nav is not None else None
        content: y.Node = (
            [nav, y.div(class_="hx-canvas-shell__page")[body]]
            if placement == "sidebar"
            else body
        )

        return y.body(
            data_hx_page_template="canvas-shell",
            data_hx_mode=self.mode,
            data_hx_navigation=placement,
        )[
            y.header[
                y.div(class_="hx-canvas-shell__header")[
                    y.a(href="/", class_="hx-brand")[
                        y.img(src=self.brand_image_src, alt=self.brand_image_alt),
                        y.span(class_="hx-brand__title")[title],
                    ],
                    y.div(class_="hx-canvas-shell__header-end")[
                        y.div(class_="hx-canvas-shell__header-content")[header_content],
                        settings_menu(self.settings),
                    ],
                ],
                nav if placement == "tabs" else None,
            ],
            y.main[y.div(class_="hx-canvas-shell__content")[content]],
            drawer(top="var(--hx-sticky-top)"),
            # Second drawer, stacked above the primary one (see AppShell).
            drawer(
                id=POPUP_DRAWER_CONTENT_ID,
                class_="hx-drawer--popup",
                top="var(--hx-sticky-top)",
            ),
            notifications(top="var(--hx-sticky-top)"),
            notification_error_template(),
        ]
