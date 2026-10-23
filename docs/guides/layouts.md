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

## Sticky offset

Page templates publish the height of what they pin to the top of the viewport as `--hx-sticky-top`, so sticky elements in the page know where to stop:

- `AppShell`: the top bar, plus the page header when the page has one.
- `CanvasShell`: the top bar.
- Without a shell it is `0px` (default in `theme.css`).

Use it for your own sticky elements: `position: sticky; top: var(--hx-sticky-top);`. Table headers (`--hx-table--sticky-top`), page-section headers and the aside of `split_layout` derive their offsets from it.

## Split layout

`split_layout` puts a main column next to an aside on the right (22rem). The aside sticks below `--hx-sticky-top` while the main column scrolls, so it works the same in both shells:

```python
c.split_layout(
    main=y.fragment[overview_card, documents_card],
    aside=history_card,
)
```

Below 58rem of **layout** width the columns stack and the aside scrolls with the page, after the main column. The breakpoint is a container query, so AppShell's sidebar is taken into account. An aside taller than the viewport scrolls on its own. See the "Split Layout" page in `samples/app_shell_layout` and `/dossier` in `samples/canvas_layout`.

## Cards

`card` is a box built by composition. Put its parts in and the CSS places them, drawing a thin line between consecutive parts:

```python
c.card[
    c.card.header[
        c.card.title[y.h2["Zusammenfassung"]],
        c.card.subtle["Jeder Satz mit Quelle"],          # on the title line
        c.card.subtitle["Aktualisiert am 15.03.2026"],   # always a second line
        c.card.actions[c.button("Bearbeiten")],          # right
    ],
    c.card.section[c.card.label[y.h3["Ausgangslage"]], y.p[...]],
    c.card.list[
        c.card.item[
            c.card.link(href="/dokument/1")["IV-Anmeldung"],   # whole row clickable
            c.card.subtle["Eingang 15.03.2026"],
        ],
    ],
    c.card.footer[c.button("Übernehmen", appearance="primary")],
]
```

- The heading level in `card.title` sets its size: `y.h1` is the page title (larger, with more room in the header, e.g. the person on a dossier), `y.h2` the regular card title, `y.h3` and `y.h4` get smaller.
- `card.link` / `card.button` make a whole `card.item` clickable by stretching an invisible overlay across it (no JavaScript). Other links and buttons in the item stay clickable on their own.
- `card(open=False)[...]` or `card(open=True)[...]` makes the card collapsible via a native `<details>`: the header becomes the toggle. It must be the first part and should not contain `card.actions`.
- `card.group[...]` is an unpadded block, typically a `card.label` above a `card.list`, so the rows run edge to edge. `card.group(open=False)[...]` makes a group collapsible the same way, with its own `card.header` as the toggle. A card can hold any number of (collapsible) groups.
- In the default design the card has a border and a small radius; in the canvas design it is a white box with a large radius on the grey canvas.

See the "Card" page in `samples/components` and `/dossier` in `samples/canvas_layout`.

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
