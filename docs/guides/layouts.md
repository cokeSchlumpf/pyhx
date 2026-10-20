# Layouts & Templates

A **page template** is what wraps your page bodies in the surrounding chrome — `<html>`, `<head>`, navigation, footer, and so on. PyHX comes with a minimal default (`Skeleton`) and lets you swap in your own.

## The `PageTemplate` protocol

A page template is any async callable matching this signature:

```python
from htpy import Node
from pyhx.core import PageTemplate, RequestContext

class PageTemplate(Protocol):
    async def __call__(
        self,
        *,
        request: RequestContext,
        app_title: str,
        page_title: str | None,
        body: Node,
        navigation: dict[str, NavFn],
    ) -> Node: ...
```

The template receives:

- `request` — the current request context (useful for things like reading the URL, headers, or user identity).
- `app_title` — the title you passed to `WebApp(title=...)`.
- `page_title` — the page's `title` (or `None` if the page chose to omit it).
- `body` — the htpy node returned by the page handler.
- `navigation` — the dict of registered navigation factories, keyed by slot name.

It returns a single `htpy.Node` for the full HTML document.

## The default: `Skeleton`

If you don't configure a template, PyHX uses `Skeleton`:

```python
class Skeleton(PageTemplate):
    async def __call__(
        self, *, request, app_title, page_title, body, navigation,
    ) -> Node:
        return y.html[
            y.head[y.title[f"{page_title} - {app_title}"]],
            y.body[await render_nav(navigation.get("main")), body],
        ]
```

It renders a `<head>` with a combined title, then the `"main"` navigation slot (if registered) followed by the page body. That's it — no styling, no metadata, no scripts. It's a starting point, not a finished design system.

## Setting a custom template

Pass your template to `WebApp(default_page_template=...)`:

```python
import htpy as y
from pyhx.core import WebApp

class MyLayout:
    async def __call__(
        self, *, request, app_title, page_title, body, navigation,
    ) -> y.Node:
        title = f"{page_title} | {app_title}" if page_title else app_title
        return y.html[
            y.head[
                y.title[title],
                y.link(rel="stylesheet", href="/static/app.css"),
            ],
            y.body[
                y.header[y.h1[app_title]],
                y.main[body],
            ],
        ]

app = WebApp(title="My App", default_page_template=MyLayout())
```

Templates are plain objects; anything callable with the right signature works, including a plain `async def` function.

## Designs

Every page template declares the **design** its components render in, via a `design` attribute typed as `Design` (`"plain"`, `"default"` or `"canvas"`):

- `Skeleton` is `"plain"` by default. Templates built on top of it pass their own design through: `Skeleton(design=self.design, ...)`.
- `AppShell` is `"default"`.
- `CanvasShell` is `"canvas"`.

The design is rendered as `data-hx-design` on the `<html>` element, so stylesheets can restyle components per design (`[data-hx-design="canvas"] .hx-button { … }`). Components that need different markup read it with `RequestContext.get_design()`; app code can use `hx.design`:

```python
from pyhx.core import RequestContext, hx

if RequestContext.get_design() == "canvas":   # in components
    ...

if hx.design == "canvas":                     # in app code
    ...
```

Both read the app's **default** page template, so they return the same value in page and fragment requests. A per-page `page_template` override does not change it — use one design per app. For templates without a `design` attribute both return `"plain"`; outside a request only `RequestContext.get_design()` works (it returns `"plain"`), while `hx` raises because no `WebApp` is set.

Branch only on designs that render differently and let all others fall through to the default rendering.

## `CanvasShell`

`CanvasShell` is the page template of the `canvas` design: a white top bar above a grey canvas, without sidebar or footer. Pages place their own breadcrumbs and content on the canvas.

```python
import htpy as y
import pyhx.components as c
from pyhx.core import RequestContext, WebApp
from pyhx.page_templates import CanvasShell

def header_content() -> y.Node:          # evaluated per request
    return RequestContext.get().user.display_name

app = WebApp(
    title="Fallbearbeitung",
    default_page_template=CanvasShell(header_content=header_content),
)

@app.page("/dossiers/{id}", title="Dossier")
async def dossier(id: str) -> y.Node:
    return y.div[
        c.breadcrumbs(y.a(href="/")["Meine Dossiers"], id),
        ...,
    ]
```

- `header_content` — right side of the top bar; a node, or a zero-argument function (sync or async) evaluated per request. Pass a list of items; the shell draws a thin separator line between them.
- `mode` — width of the content area: `"centered"` (at most 72rem, default), `"wide"` (at most `--hx-container-width-wide`) or `"full"` (full width, no padding). Change it per page with `page_template=CanvasShell(mode="full")`.
- `brand_img_src` / `brand_img_alt` — logo and title on the left, as in `AppShell`. Defaults to the PyHX mark (`/static/images/pyhx_mark.svg`).
- `favicon` — defaults to the PyHX mark as well.

Drawers, notifications and htmx error toasts are mounted like in `AppShell`, so drawer-based components keep working. The design's token values live in `static/css/themes/canvas.css`; see `samples/canvas_layout` for a runnable example.

## Per-page overrides

A single page can override the layout for one response by returning a `PageResponse`:

```python
from pyhx.core import PageResponse
from pyhx.core.primitives import omit

@app.page("/print", title="Printable")
async def printable() -> PageResponse:
    return PageResponse(
        node=y.h1["Printable view"],
        page_template=omit,   # render the body without any layout
    )
```

- `page_template=None` (the default) uses the app's default template.
- `page_template=<some template>` uses that template just for this response.
- `page_template=omit` skips the template entirely and returns the body as-is.

Similarly, `page_title` accepts `None`, a string, or `omit` to skip the title.
