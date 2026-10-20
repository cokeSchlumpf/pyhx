from typing import Any, Literal, cast

import htpy as y

from ..components.layouts import (
    POPUP_DRAWER_CONTENT_ID,
    drawer,
    notification_error_template,
    notifications,
)
from ..core.primitives import SyncOrAsyncValue, resolve_value
from ..core.request_context import RequestContext
from ..core.templates.nav import AppNavFn
from ..core.templates.page_template import Design, PageTemplate
from ..core.templates.skeleton import Skeleton

CanvasShellMode = Literal["centered", "wide", "full"]
"""Width of the content area.

- ``centered`` — centered column of at most 72rem (lists, case overviews).
- ``wide`` — centered column of at most ``--hx-container-width-wide``.
- ``full`` — full viewport width without padding (e.g. a document viewer).
"""


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
    """

    design: Design = "canvas"

    def __init__(
        self,
        *,
        brand_img_alt: str | None = None,
        brand_img_src: str = "/static/images/pyhx_mark.svg",
        favicon: str = "/static/images/pyhx_mark.svg",
        header_content: SyncOrAsyncValue[y.Node] = None,
        mode: CanvasShellMode = "centered",
        stylesheets: tuple[str, ...] = (),
        scripts: tuple[str, ...] = (),
    ) -> None:
        self.brand_image_alt = brand_img_alt
        self.brand_image_src = brand_img_src
        self.favicon = favicon
        self.header_content = header_content
        self.mode = mode
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
            design=self.design,
            favicon=self.favicon,
            stylesheets=(
                "/static/css/fonts.css",
                "/static/css/pyhx.css",
                "/static/css/themes/canvas.css",
                "/static/css/page-templates/canvas-shell.css",
                *self.stylesheets,
            ),
            scripts=("/static/js/pyhx.notifications.js", *self.scripts),
        )

        return await skeleton(
            request=request,
            app_title=app_title,
            page_title=page_title,
            body=await self._render_page(app_title=app_title, body=body),
            navigation=navigation,
        )

    async def _render_page(self, *, app_title: str, body: y.Node) -> y.Node:
        title = self.brand_image_alt or app_title
        # `y.Node` itself contains awaitables and iterables, so mypy can't
        # solve `resolve_value`'s type parameter from it; same cast as in
        # DataSection.
        header_content: y.Node = await resolve_value(
            cast(SyncOrAsyncValue[Any], self.header_content)
        )

        return y.body(data_hx_page_template="canvas-shell", data_hx_mode=self.mode)[
            y.header[
                y.div(class_="hx-canvas-shell__header")[
                    y.a(href="/", class_="hx-brand")[
                        y.img(src=self.brand_image_src, alt=self.brand_image_alt),
                        y.span(class_="hx-brand__title")[title],
                    ],
                    y.div(class_="hx-canvas-shell__header-content")[header_content],
                ],
            ],
            y.main[y.div(class_="hx-canvas-shell__content")[body]],
            drawer(top="var(--header--height)"),
            # Second drawer, stacked above the primary one (see AppShell).
            drawer(
                id=POPUP_DRAWER_CONTENT_ID,
                class_="hx-drawer--popup",
                top="var(--header--height)",
            ),
            notifications(top="var(--header--height)"),
            notification_error_template(),
        ]
