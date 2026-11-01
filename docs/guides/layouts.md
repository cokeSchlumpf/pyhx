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

`CanvasShell` is the page template of the `canvas` design: a white top bar above a grey canvas, without footer and — by default — without navigation. Pages place their own breadcrumbs and content on the canvas.

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
- `main_navigation` — `None` (default, no navigation), `"tabs"` or `"sidebar"`; see below.
- `navigation_slot` — the navigation slot to show, `"main"` by default.

### Main navigation

The menus come from `hx.navigation`, as in `AppShell`: each slot is a named menu, a list of items or a dict of labelled groups (`""` for items without a group). The template decides whether and where a slot appears:

- `main_navigation="tabs"` — a row of tabs below the top bar, part of the sticky header; for a handful of top-level areas. Groups open as a dropdown.
- `main_navigation="sidebar"` — a column on the canvas left of the content, sticky below the top bar; for many items in labelled groups, e.g. admin pages. On a phone it becomes a horizontally scrolling row above the content.

Choose it for the whole app with `default_page_template`, or per page with `PageResponse(page_template=...)`. With `navigation_slot`, one app can show tabs on its pages and a separate sidebar on its admin pages:

```python
app.navigation.set([app.nav_item(dossiers), app.nav_item(inbox)])          # slot "main"
app.navigation.set(
    {"": [app.nav_item(admin, full_match=True)], "Benutzer": [app.nav_item(users)]},
    slot="admin",
)

ADMIN = CanvasShell(main_navigation="sidebar", navigation_slot="admin")

@app.page("/admin/users", title="Benutzer")
async def users() -> PageResponse:
    return PageResponse(node=..., page_template=ADMIN)
```

The active item is marked from the URL (`full_match=False` also marks sub-pages). A slot without a menu renders no navigation.

### Form controls

Forms need no extra code on the canvas: text inputs, selects, textareas, checkboxes, radios and switches, and the components built on them (`form_field`, `DataForm`, `dropdown`, `drawer_radio`, `drawer_select`, `select_fieldset`, `segment_control`), take the look of the design:

- Fields and buttons share one height, 36px (`button(..., size="sm")` 28px), with 14px text and an 8px radius; the label sits above the field, help text below it.
- The accent is the text colour, not blue: focus, checked controls, primary buttons and the checked option of a segment control.
- States: hover darkens the border; focus shows a dark border and a ring; `aria-invalid="true"` an orange border; `readonly` a dashed border; `disabled` a grey field.

Contrast follows WCAG 2.2 AA: control borders reach 3:1 against white and the canvas (`#878787`, 1.4.11), help text and error text 4.5:1 (`--hx-color-danger-700` for errors, since the design's orange `--hx-color-danger-600` only reaches 3.58:1). The values are Pico's form tokens in `static/css/themes/canvas.css`; the rules Pico has no token for are in `static/css/pyhx/elements/form.css` and the component stylesheets, under `[data-hx-design="canvas"]`. The page `/forms` of `samples/canvas_layout` shows every control in every state.

### Compact forms

Drawers and asides are narrow, so their forms are compact: 32px fields with a 13px label, help text 4px below, fields 12px apart. The place decides, no code is needed: every `form_field` and `DataForm` in a drawer or in the aside of `split_layout` is compact. `size` overrides the place: `form_field(..., size="sm")`, `DataForm(..., size="sm")` or `DataFormDrawer(..., size="sm")` makes a field or form compact anywhere, `size="md"` keeps the full size in a drawer or aside. In the default design `size` has no visible effect.

### Label position

`label_position` decides where a field's label sits, on `form_field`, `DataForm` and `DataFormDrawer`:

- `"left"` — the label in a 128px column left of the field, while the **field's own cell** is at least 360px wide; in a narrower cell (a column of a two-column form, a phone) the label moves above the field by itself. It works with `columns` and `template_areas`: each field decides for its own cell.
- `"top"` — the label always above the field; the form keeps its `columns`, in a drawer too.
- `None` (default) — above the field; a compact form of the canvas design (in a drawer or an aside) shows one field per row with the labels left where the cell has room. Forms with `template_areas` keep their layout.

`label_position` is layout only and works in both designs; colours and sizes come from the design.

### DataPage and drawers

A `DataPage` takes the look of the design without code changes:

- Breadcrumbs, title and actions (e.g. "Filter & Sort", create) sit on the canvas, not in a band; neutral buttons are white with the 3:1 border.
- The table is a white card (12px radius, thin border) with a light header row; a table directly in the content column gets the card, tables inside cards keep their look.
- The edit and create drawers have a header with the title and a close button, a scrolling body with the compact form, and 28px buttons in the footer.

`form_size` and `form_label_position` on `DataPage` and `DataSection` are passed to both drawers (as `size` and `label_position`), e.g. `DataPage(..., form_label_position="top")` for a drawer form that keeps its two columns.

In both designs:

- The drawer of `DataFormDrawer` (the edit and create drawers of `DataPage` and `DataSection`) keeps its header on top and its footer at the bottom while the form scrolls: delete on the left as an underlined text button in `--hx-color-danger-700`, cancel and submit on the right. Delete still asks for confirmation in the popup drawer. The default design keeps its colours, labels on top and the form's columns.
- An open drawer and its backdrop are drawn above the page (page header and sticky table header included) and below the top bar. The page behind it doesn't scroll, also not when the drawer's content ends or fits.
- Focus moves into a drawer when it opens and back when it closes; Esc closes the topmost drawer.

`/data-page`, `/data-page-detail` (create drawer with `form_label_position="top"`) and `/forms` (a form with `label_position="left"`) of `samples/canvas_layout` show it.

Drawers, notifications and htmx error toasts are mounted like in `AppShell`, so drawer-based components keep working. The design's token values live in `static/css/themes/canvas.css`; see `samples/canvas_layout` for a runnable example.

## Sticky offset

Page templates publish the height of what they pin to the top of the viewport as `--hx-sticky-top`, so sticky elements in the page know where to stop:

- `AppShell`: the top bar, plus the page header when the page has one.
- `CanvasShell`: the top bar, plus the tab row with `main_navigation="tabs"`.
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
