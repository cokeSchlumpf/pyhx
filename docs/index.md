# PyHX

**WebApps with HTMX and Python.**

PyHX is a thin, declarative layer on top of [FastAPI](https://fastapi.tiangolo.com/) and [htpy](https://htpy.dev/) for building server-rendered web applications driven by [HTMX](https://htmx.org/). You write Python functions that return HTML trees; PyHX wires them up as full pages, HTMX fragments, and reusable components.

## Why PyHX?

If you want HTMX-style interactivity without a separate JavaScript build, two things normally get in the way: templating syntax (Jinja, Mako) and the ceremony of declaring partial endpoints alongside their pages. PyHX removes both:

- **HTML as Python expressions** — htpy lets you compose markup with normal Python data structures and type checking, with no string templates.
- **Fragments as first-class citizens** — declare an HTMX endpoint with a decorator, return a `Node`, and PyHX hands the HTML back with the right content type.
- **Components co-locate logic and partials** — a `@component` is a callable that produces HTML *and* exposes its own fragment routes under a stable prefix.

## A taste

```python
import htpy as y
from pyhx.core import WebApp

app = WebApp(title="Hello")

@app.page("/", title="Home")
async def home() -> y.Node:
    return y.div[
        y.h1["Hello, PyHX"],
        y.button(hx_get="/clock", hx_swap="outerHTML")["What time is it?"],
    ]

@app.fragment.get("/clock")
async def clock() -> y.Node:
    from datetime import datetime
    return y.time[datetime.now().isoformat()]

fastapi_app = app.create_app()
```

Run with any ASGI server (`uvicorn module:fastapi_app`) and the button swaps itself for the current time on click — no JavaScript code on your side.

## Where to go next

- [Installation](getting-started/installation.md)
- [Your First App](getting-started/first-app.md)
- Concepts: [Pages](concepts/pages.md), [Fragments & HTMX](concepts/fragments.md), [Components](concepts/components.md)
- Guides: [Routing & Paths](guides/routing.md), [Routers](guides/routers.md), [Navigation](guides/navigation.md), [Layouts & Templates](guides/layouts.md), [User Authentication](guides/user-authentication.md)
