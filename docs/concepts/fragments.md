# Fragments & HTMX

A **fragment** is a small HTML response designed to be swapped into an existing page by HTMX. Fragments are how PyHX makes interactivity feel like server-rendered HTML: instead of returning JSON to a client-side framework, you return HTML to the part of the page that asked for it.

## Declaring a fragment

```python
import htpy as y
from pyhx.core import WebApp

app = WebApp(title="Demo")

@app.fragment.get("/now")
async def now() -> y.Node:
    from datetime import datetime
    return y.time[datetime.now().isoformat()]
```

`app.fragment` is a factory with one method per HTTP verb:

| Method | Registers |
| --- | --- |
| `app.fragment.get(path)` | `GET path` |
| `app.fragment.post(path)` | `POST path` |
| `app.fragment.put(path)` | `PUT path` |
| `app.fragment.patch(path)` | `PATCH path` |
| `app.fragment.delete(path)` | `DELETE path` |

Like pages, the handler must be `async` and return either a `Node` or a `FragmentResponse`.

## How HTMX picks it up

A fragment is just an endpoint that returns HTML without a surrounding layout. Wire it to an element in your page using HTMX attributes:

```python
@app.page("/", title="Home")
async def home() -> y.Node:
    return y.div[
        y.div(id="clock")["—"],
        y.button(
            hx_get="/now",
            hx_target="#clock",
            hx_swap="innerHTML",
        )["Refresh"],
    ]
```

When the button is clicked, HTMX issues `GET /now`, takes the response, and swaps it into `#clock`. PyHX gives back exactly what the handler returned — no template wrapping, no `<html>`/`<body>`.

## `FragmentResponse`

Return a `FragmentResponse` when you need to set status, headers, or background tasks:

```python
from http import HTTPStatus
from pyhx.core import FragmentResponse

@app.fragment.post("/saved")
async def saved() -> FragmentResponse:
    return FragmentResponse(
        node=y.span["Saved."],
        status_code=HTTPStatus.CREATED,
        headers={"HX-Trigger": "saved"},
    )
```

Fields mirror `PageResponse` — `node`, `status_code`, `headers`, `media_type`, `background`.

## Redirecting to another page

A fragment can never *render* a different page: HTMX swaps whatever comes back into the element that issued the request, so a full page would land inside your `#clock` div. A plain `303 + Location` doesn't help either — HTMX's XHR follows the redirect transparently and swaps the *redirected* page's HTML into the same element.

To send the browser somewhere else, use `FragmentResponse.redirect()`. It returns an empty `200` carrying the `HX-Redirect` header, which tells HTMX to do a real `window.location` navigation:

```python
@app.fragment.post("/orders")
async def create_order() -> FragmentResponse:
    order_id = await orders.create()
    return FragmentResponse.redirect(f"/orders/{order_id}")
```

From a plain (non-HTMX) page handler, use `PageResponse.redirect()` instead — it sends the `303 + Location` that browsers act on. The two are not interchangeable: browsers ignore `Location` on a `2xx`, and HTMX swallows a `3xx`.

For an ordinary "clicking this navigates there" link, prefer a plain `<a href>` over a fragment round-trip — it costs no request and keeps middle-click and open-in-new-tab working.

## Module-level fragments with `hx`

Sometimes you want to declare fragments at import time, separate from a particular `WebApp` instance. PyHX provides the `hx` proxy for exactly this:

```python
import htpy as y
from pyhx.core import hx

@hx.fragment.get("/ping")
async def ping() -> y.Node:
    return y.span["pong"]
```

These fragments register with a process-global fragment registry. When you later construct a `WebApp`, it subscribes to the registry and picks them up automatically — including ones declared in modules imported before the `WebApp` was instantiated.

This is the same mechanism components rely on; see [Components](components.md).

## Path parameters

Fragments use the same `{name}` placeholder syntax as pages. See [Routing & Paths](../guides/routing.md) for the rules.

```python
@app.fragment.get("/users/{user_id}/badge")
async def user_badge(user_id: str) -> y.Node:
    return y.span(cls="badge")[user_id]
```
