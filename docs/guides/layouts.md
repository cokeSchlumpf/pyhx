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
