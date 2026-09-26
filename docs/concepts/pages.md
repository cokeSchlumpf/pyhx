# Pages

A **page** is a full HTML response served at a URL. Pages are the entry points to your app — they're what the browser sees on a fresh navigation. Each page is declared by decorating an `async` function with `@app.page(...)`.

## Declaring a page

```python
import htpy as y
from pyhx.core import WebApp

app = WebApp(title="Docs Demo")

@app.page("/", title="Home")
async def home() -> y.Node:
    return y.h1["Hello"]
```

`@app.page(path, *, title, icon=None)` registers a `GET` route. The decorated function must be `async` and return either:

- an `htpy.Node` — PyHX wraps it in the default `PageResponse`, or
- a `PageResponse` — when you need to customize status, headers, layout, or title.

## What gets rendered

When a request comes in, PyHX:

1. Calls the handler with any path parameters and an optional `Request` injection.
2. Wraps the returned `Node` in a `PageResponse` (if it isn't one already).
3. Passes the node through the active page template (default: `Skeleton`), which adds `<html>`, `<head>`, navigation, and so on.
4. Sends the rendered HTML to the client.

See [Layouts & Templates](../guides/layouts.md) for how to customize step 3.

## `PageResponse`

Return a `PageResponse` when you need more than a plain body:

```python
from http import HTTPStatus
from pyhx.core import PageResponse

@app.page("/missing", title="Missing")
async def missing() -> PageResponse:
    return PageResponse(
        node=y.h1["Not here"],
        status_code=HTTPStatus.NOT_FOUND,
        headers={"X-Reason": "missing"},
    )
```

Fields:

| Field | Default | Purpose |
| --- | --- | --- |
| `node` | required | The body content. |
| `status_code` | `200 OK` | HTTP status. |
| `headers` | `None` | Extra response headers. |
| `media_type` | `"text/html"` | `Content-Type`. |
| `background` | `None` | Starlette background task. |
| `page_template` | `None` | Override the layout for this response (use `omit` to skip the layout entirely). |
| `page_title` | `None` | Override the title used by the layout. |

## Path parameters

Paths use the same brace syntax as the rest of PyHX (see [Routing & Paths](../guides/routing.md)):

```python
@app.page("/users/{user_id}", title="User")
async def user(user_id: str) -> y.Node:
    return y.h1[f"User {user_id}"]
```

Variables are extracted by name. Use lowercase identifiers — PyHX's `PathTemplate` enforces `[a-z][a-z0-9_]*`.

## Accessing the request

If your handler declares a `request: Request` parameter, FastAPI injects the current request. PyHX also exposes a context-local accessor for use deeper in the call stack:

```python
from pyhx.core import RequestContext

@app.page("/me", title="Me")
async def me() -> y.Node:
    ctx = RequestContext.get()
    return y.div[f"You requested {ctx.request.url.path}"]
```

`RequestContext.get()` works anywhere inside a request — render functions, components, navigation factories — without threading the request through every call.

## Declaring pages outside the WebApp

When you want to declare pages in a sibling module without importing the live `WebApp`, use a `WebAppRouter`. The decorator surface is the same — `@router.page(path, *, title, icon=None)` — and the top-level app attaches the router's pages via `app.include_router(router, prefix="...")`. See [Routers — Splitting an App Across Modules](../guides/routers.md).
