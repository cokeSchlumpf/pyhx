# API Endpoints

An **API endpoint** is a route that returns a raw FastAPI `Response` instead of HTML. Where [pages](pages.md) and [fragments](fragments.md) return an htpy `Node` that PyHX renders, `app.api` hands you full control over the response — JSON, streaming, files, custom status codes and headers — while still giving your handler access to the per-request [`RequestContext`](../guides/user-authentication.md).

Reach for it when you need a machine-facing endpoint (a JSON API, a webhook receiver, a file download) rather than an HTML view.

## Declaring an API endpoint

```python
from fastapi import Response
from fastapi.responses import JSONResponse
from pyhx.core import WebApp

app = WebApp(title="Demo")

@app.api.get("/api/now")
async def now() -> Response:
    from datetime import datetime
    return JSONResponse({"now": datetime.now().isoformat()})
```

`app.api` is a factory with one method per HTTP verb:

| Method | Registers |
| --- | --- |
| `app.api.get(path)` | `GET path` |
| `app.api.post(path)` | `POST path` |
| `app.api.put(path)` | `PUT path` |
| `app.api.patch(path)` | `PATCH path` |
| `app.api.delete(path)` | `DELETE path` |

## Handler contract

- **Async only.** Handlers must be `async def`; PyHX `await`s them.
- **Parameters work exactly like a standard FastAPI endpoint.** Declare path parameters, query parameters, Pydantic request bodies, `Depends(...)`, `Header(...)`, etc. — PyHX preserves your signature, so FastAPI's dependency injection behaves as usual. You do *not* need to add a `request: Request` parameter (though you may).
- **Return a `Response`.** Return `JSONResponse`, `StreamingResponse`, `FileResponse`, `PlainTextResponse`, or any `Response` subclass. Unlike fragments/pages there is no `Node` wrapping — what you return is sent verbatim.

```python
@app.api.get("/api/items/{item_id}")
async def get_item(item_id: str, q: str | None = None) -> Response:
    return JSONResponse({"item_id": item_id, "q": q})
```

See [Routing & Paths](../guides/routing.md) for the `{name}` placeholder rules, shared with pages and fragments.

## Accessing the request context

This is the key difference from registering a route directly on the underlying FastAPI app (e.g. via `configure_fast_api_app`). PyHX wraps every `app.api` handler so the [`RequestContext`](../guides/user-authentication.md) is established *before* your code runs. That means `RequestContext.get()` and the authentication accessors work inside the handler with no extra wiring:

```python
from pyhx.core import RequestContext
from pyhx.addons.user_authentication import require_authenticated_user

@app.api.get("/api/me")
async def me() -> Response:
    user = require_authenticated_user()   # raises NotAuthenticated if anonymous
    ctx = RequestContext.get()            # full per-request context
    return JSONResponse({"id": user.id, "name": user.display_name})
```

A plain FastAPI route added outside PyHX does **not** get this — `RequestContext.get()` would raise `LookupError` there because the context is only seeded by PyHX's route wrappers. Using `app.api` is the supported way to get a custom endpoint with full context access.

## Error handling

Like pages and fragments, if your handler raises an exception type that the app has a registered FastAPI `exception_handler` for, PyHX re-raises so that handler runs. For example, `NotAuthenticated` raised by `require_authenticated_user()` is converted into a login redirect when [user authentication](../guides/user-authentication.md) is configured. Unhandled exceptions fall through to PyHX's error response.

## OpenAPI / `/docs`

Unlike pages and fragments (which are excluded from the schema), API endpoints are **included in the OpenAPI schema** and show up in FastAPI's interactive docs at `/docs`. Because your handler signature is preserved, path and query parameters are documented automatically.

## Routers

`WebAppRouter` exposes the same `api` factory, so you can declare API endpoints in modules that don't import a live `WebApp` and attach them later under a prefix. See [Routers](../guides/routers.md).

```python
from fastapi.responses import PlainTextResponse
from pyhx.core import WebAppRouter

router = WebAppRouter()

@router.api.get("/ping")
async def ping() -> Response:
    return PlainTextResponse("pong")

# elsewhere
app.include_router(router, prefix="/api")   # serves GET /api/ping
```

Prefixes compose across nested `include_router` calls, exactly as they do for pages and fragments.
