from typing import Annotated, Literal

import htpy as y
from commons.settings import AppSettings
from commons.users import AnonymousUser
from fastapi import Form
from markupsafe import Markup

from ..components.layouts import (
    POPUP_DRAWER_CONTENT_ID,
    drawer,
    notification_card,
    notifications,
)
from ..components.primitives import pill
from ..core import component
from ..core.primitives import Omit, classnames, htmx
from ..core.request_context import RequestContext
from ..core.templates.nav import AppNavFn, NavItem
from ..core.templates.nav_renderer import NavRenderer
from ..core.templates.page_template import PageTemplate
from ..core.templates.skeleton import Skeleton

# Hidden <template> id the JS in pyhx.app-shell.js clones on htmx error events.
# Lives here (next to the AppShell that renders the template) because the JS
# that uses it ships with this page template, not with the notifications
# component.
APP_SHELL_NOTIFICATION_ERROR_TEMPLATE_ID = "hx-notification__error-template"


@component
def footer_tooltip(label: str | None = None) -> y.Node:
    return y.div(
        id="app-shell__footer-tooltip", **htmx(hx_swap_oob="outerHTML", as_dict=True)
    )[pill(label, appearance="info", style="text-transform: none") if label else None]


@footer_tooltip.fragments.post("/")
async def render_tooltip(label: Annotated[str | None, Form()] = None):
    return footer_tooltip(label)


class AppShellNavRenderer(NavRenderer):
    def render_item(
        self,
        *,
        item: NavItem,
        is_active: bool,
        in_group: bool,
    ) -> y.Node:
        # Wrap label text in <span> so compact-mode CSS can selectively hide it
        # while keeping the leading icon visible as an icon rail.
        inner: list[y.Node] = []
        if item.icon:
            inner.append(y.i(data_feather=item.icon))
        inner.append(y.span[item.label])

        return y.li(role="treeitem")[
            y.a(
                href=str(item.to),
                **classnames({"active": is_active}),
            )[inner]
        ]

    def render_group(
        self, *, label: str, items: list[y.Node], has_active: bool
    ) -> y.Node:
        return y.li(role="group", **classnames({"active": has_active}))[
            y.h3[label], y.ul[items]
        ]

    def render_flat(self, *, items: list[y.Node]) -> y.Node:
        return items

    def render_root(self, *, slot: str, sections: list[y.Node]) -> y.Node:
        return y.ul(role="menu")[sections]

    def render_empty(self, *, slot: str) -> y.Node:
        return y.fragment[[]]


class AppShell(PageTemplate):
    def __init__(
        self,
        *,
        brand_img_alt: str | None = None,
        brand_img_src: str = "/static/images/pyhx_white.svg",
        mode: Literal["page", "app"] = "page",
        sidebar_content: y.Node | None = None,
        footer_content_left: y.Node | None | Omit = None,
        main_navigation: bool = True,
        user_menu: bool = False,
        compact_main_navigation: bool = False,
        login_url: str = "/login",
        logout_url: str = "/logout",
        stylesheets: tuple[str, ...] = (),
        scripts: tuple[str, ...] = (),
    ) -> None:
        self.brand_image_alt = brand_img_alt
        self.brand_image_src = brand_img_src
        self.compact_main_navigation = compact_main_navigation
        self.footer_content_left = footer_content_left
        self.login_url = login_url
        self.logout_url = logout_url
        self.mode = mode
        self.main_navigation = main_navigation
        self.user_menu = user_menu
        self.sidebar_content = sidebar_content
        self.stylesheets = stylesheets
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
        skeleton = Skeleton(
            stylesheets=(
                "/static/css/pyhx.css",
                "/static/css/page-templates/app-shell.css",
                *self.stylesheets,
            ),
            scripts=("/static/js/pyhx.app-shell.js", *self.scripts),
            head_extras=(
                y.script(type="text/javascript")[
                    Markup(f"TOOLTIP_URL = '{render_tooltip.url()}';")
                ],
            ),
        )

        return await skeleton(
            request=request,
            app_title=app_title,
            page_title=page_title,
            body=await self._render_page(
                request=request,
                app_title=app_title,
                body=body,
                navigation=navigation,
            ),
            navigation=navigation,
        )

    async def _render_page(
        self,
        *,
        request: RequestContext,
        app_title: str,
        body: y.Node,
        navigation: AppNavFn,
    ) -> y.Node:
        nav_renderer = AppShellNavRenderer()
        app_title = self.brand_image_alt or f"{app_title}"

        if self.footer_content_left is None:
            app_settings = AppSettings.read()
            footer_content_left: y.Node = y.div[
                pill(app_settings.environment, appearance="warning"),
                " ",
                y.code[app_settings.version],
            ]
        elif isinstance(self.footer_content_left, Omit):
            footer_content_left = y.fragment[""]
        else:
            footer_content_left = self.footer_content_left

        return y.body(
            data_hx_page_template="app-shell",
            data_hx_mode=self.mode,
            data_hx_main_menu=str(self.main_navigation).lower(),
        )[
            (
                [
                    y.input(
                        type="checkbox", id="hx-menu__toggle", class_="hx-menu__toggle"
                    ),
                    y.input(
                        type="checkbox",
                        id="hx-menu__compact",
                        class_="hx-menu__toggle",
                        checked=self.compact_main_navigation,
                    ),
                ]
                if self.main_navigation
                else None
            ),
            (
                y.input(
                    type="checkbox", id="hx-user-menu__toggle", class_="hx-menu__toggle"
                )
                if self.user_menu
                else None
            ),
            y.header[
                y.div[
                    # Burger menu button — mobile (opens sidepanel)
                    (
                        y.label(
                            for_="hx-menu__toggle",
                            class_="hx-menu-button hx-menu-button--icon",
                            aria_label="Open menu",
                        )[y.i(data_feather="menu")]
                        if self.main_navigation
                        else None
                    ),
                    # Burger menu button — desktop (toggles compact mode)
                    (
                        y.label(
                            for_="hx-menu__compact",
                            class_="hx-menu-button hx-menu-button--icon",
                            aria_label="Toggle compact menu",
                        )[y.i(data_feather="menu")]
                        if self.main_navigation
                        else None
                    ),
                    # Brand logo
                    y.a(href="/", class_="hx-brand")[
                        y.img(src=self.brand_image_src, alt=self.brand_image_alt),
                        y.span(class_="hx-brand__title")[app_title],
                    ],
                ],
                y.div[
                    # User menu
                    y.button(aria_label="Settings", title="Application Settings")[
                        y.i(data_feather="settings")
                    ],
                    y.button(aria_label="Help", title="Get Help")[
                        y.i(data_feather="help-circle")
                    ],
                    self._render_user_menu(request) if self.user_menu else None,
                ],
            ],
            (
                y.div(class_="hx-sidepanel")[
                    y.div(class_="hx-sticky")[
                        y.nav(aria_label="main")[
                            await nav_renderer(
                                slot="main", ctx=request, navigation=navigation
                            ),
                            self.sidebar_content,
                        ],
                    ],
                    # User menu: fixed dropdown on desktop; flows inside sidepanel on mobile.
                    y.nav(aria_label="user")[
                        y.ul[
                            y.li[
                                y.a(href="#")[y.i(data_feather="settings"), "Settings"]
                            ],
                            y.li(role="separator"),
                            y.li[
                                y.a(href=self.logout_url)[
                                    y.i(data_feather="log-out"), "Logout"
                                ]
                            ],
                        ]
                    ],
                ]
                if self.main_navigation
                else None
            ),
            y.main[y.div(class_="hx-sticky")[body]],
            y.label(
                for_="hx-menu__toggle", class_="hx-menu__backdrop", aria_hidden="true"
            ),
            y.label(
                for_="hx-user-menu__toggle",
                class_="hx-user-menu__backdrop",
                aria_hidden="true",
            ),
            y.footer[footer_content_left, footer_tooltip("")],
            drawer(
                top="var(--header--height)",
                bottom="var(--footer--height)",
            ),
            # Second drawer, stacked above the primary one. Drawer-based pickers
            # (`drawer_select` / `drawer_radio`) open here so they can sit on top
            # of a form rendered in the primary drawer instead of replacing it.
            drawer(
                id=POPUP_DRAWER_CONTENT_ID,
                class_="hx-drawer--popup",
                top="var(--header--height)",
                bottom="var(--footer--height)",
            ),
            notifications(top="var(--header--height)"),
            # Skeleton cloned by the htmx-error handler in pyhx.app-shell.js
            # to surface request / network / timeout / swap failures as toasts.
            y.template(id=APP_SHELL_NOTIFICATION_ERROR_TEMPLATE_ID)[
                notification_card(
                    appearance="danger",
                    icon="alert-octagon",
                ),
            ],
        ]

    async def _render_user_menu(self, request: RequestContext) -> y.Node:
        if isinstance(request.user, AnonymousUser):
            return y.a(
                href=self.login_url,
                role="button",
                aria_label="Sign In",
                title="Sign In",
            )[y.i(data_feather="log-in"), "Sign In"]
        else:
            return y.label(
                for_="hx-user-menu__toggle",
                class_="hx-menu-button",
                aria_label="Toggle user menu",
            )[request.user.display_name, y.i(data_feather="user")]
