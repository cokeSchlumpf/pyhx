import htpy as y
from htpy import head, html, link, meta, script, title
from markupsafe import Markup

from ..request_context import RequestContext
from .nav import AppNavFn
from .page_template import PageTemplate

# Detect the browser's IANA timezone and write it to the `hx_tz` cookie so it
# rides along with every subsequent request. Refreshed on every load; the first-ever request (before any page set it) falls back to the configured default zone.
_TIMEZONE_COOKIE_SNIPPET = Markup(
    "(function(){try{var t=Intl.DateTimeFormat().resolvedOptions().timeZone;"
    'if(t){document.cookie="hx_tz="+encodeURIComponent(t)+'
    '"; path=/; max-age=31536000; samesite=lax";}}catch(e){}})();'
)


class Skeleton(PageTemplate):
    def __init__(
        self,
        stylesheets: tuple[str, ...] = (),
        scripts: tuple[str, ...] = (),
        head_extras: tuple[y.Node, ...] = (),
        favicon: str = "/static/images/favicon.svg",
    ) -> None:
        self.stylesheets = stylesheets
        self.scripts = scripts
        self.head_extras = head_extras
        self.favicon = favicon

    async def __call__(
        self,
        *,
        request: RequestContext,
        app_title: str,
        page_title: str | None,
        body: y.Node,
        navigation: AppNavFn,
    ) -> y.Node:
        # nav_renderer = NavRenderer()
        html_title = f"{page_title} | {app_title}" if page_title else app_title
        # main_nav = await nav_renderer(slot="main", ctx=request, navigation=navigation)

        return html(data_theme="light")[
            head[
                meta(charset="utf-8"),
                meta(name="viewport", content="width=device-width, initial-scale=1"),
                script[_TIMEZONE_COOKIE_SNIPPET],
                title[html_title],
                *[link(rel="stylesheet", href=href) for href in self.stylesheets],
                link(rel="icon", type="image/svg+xml", href=self.favicon),
                script(src="/static/js/htmx.min.js"),
                script(src="/static/js/htmx-ext-morph.min.js"),
                script(src="/static/js/htmx-ext-sse.min.js"),
                script(src="/static/js/htmx-ext-ws.min.js"),
                script(src="/static/js/feather.min.js"),
                script(src="/static/js/pyhx.js"),
                script(src="/static/js/pyhx.table.js"),
                script(src="/static/js/pyhx.wysiwyg-editor.js"),
                script(src="/static/js/pyhx.file-dropzone.js"),
                script(src="/static/js/pyhx.code.js"),
                script(src="/static/js/pyhx.data-form.js"),
                script(src="/static/js/pyhx.dropdown.js"),
                script(src="/static/js/pyhx.delete-confirm.js"),
                script(src="/static/js/pyhx.drawer.js"),
                script(src="/static/js/pyhx.filter-drawer.js"),
                *[script(src=src) for src in self.scripts],
                *self.head_extras,
            ],
            body,
        ]
