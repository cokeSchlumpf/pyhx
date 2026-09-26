# Your First App

This page builds a tiny PyHX application end-to-end: a page, a button, and an HTMX fragment that swaps itself in on click.

## 1. Create a `WebApp`

```python
# app.py
import htpy as y
from pyhx.core import WebApp

app = WebApp(title="Counter")
```

`WebApp` is the framework's central object. It owns the registered pages, fragments, default layout, and (eventually) the FastAPI app produced by `create_app()`.

## 2. Add a page

A page is an `async` function that returns an `htpy.Node`. Use `@app.page(...)` to attach a path and a title:

```python
@app.page("/", title="Home")
async def home() -> y.Node:
    return y.div[
        y.h1["Counter"],
        y.div(id="value")["0"],
        y.button(
            hx_get="/increment",
            hx_target="#value",
            hx_swap="innerHTML",
        )["+1"],
    ]
```

When the user hits `/`, PyHX renders the returned node through the default layout (`Skeleton`) and serves it as HTML.

## 3. Add an HTMX fragment

A fragment is a partial-HTML endpoint. The HTMX button above points at `/increment`; let's wire it up:

```python
_counter = 0

@app.fragment.get("/increment")
async def increment() -> y.Node:
    global _counter
    _counter += 1
    return y.span[str(_counter)]
```

`@app.fragment.get(...)` registers a `GET /increment` route that returns raw HTML (no layout). HTMX swaps the response into `#value`.

`@app.fragment` exposes one method per HTTP verb (`get`, `post`, `put`, `patch`, `delete`).

## 4. Expose the FastAPI app

`WebApp` doesn't run itself — call `create_app()` to materialize a `FastAPI` application:

```python
fastapi_app = app.create_app()
```

## 5. Run it

```bash
uvicorn app:fastapi_app --reload
```

Open `http://127.0.0.1:8000/`, click the button, and watch the counter increment without a full page reload.

## Where to go next

- [Pages](../concepts/pages.md) — how pages, responses, and layouts fit together.
- [Fragments & HTMX](../concepts/fragments.md) — the partial-update model in more detail.
- [Components](../concepts/components.md) — bundle HTML and fragments into reusable units.
- [Routers](../guides/routers.md) — when your app outgrows one file, split pages and fragments across modules with `WebAppRouter`.
