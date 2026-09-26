# Routers — Splitting an App Across Modules

When an app outgrows a single file, declare pages, fragments, and websockets in sibling modules using **`WebAppRouter`**. Each module owns its own router; the top-level `WebApp` attaches the routers at startup with `include_router(...)`. The pattern matches FastAPI's `APIRouter` and Flask's `Blueprint`.

## A two-file app

`pages/users.py` declares its routes against a local router, with no reference to a `WebApp`:

```python
import htpy as y
from pyhx.core import WebAppRouter

router = WebAppRouter()

@router.page("/users", title="Users")
async def users_page() -> y.Node:
    return y.div[y.h1["Users"]]

@router.page("/users/{user_id}", title="User detail")
async def user_detail(user_id: str) -> y.Node:
    return y.div[y.h1[f"User {user_id}"]]
```

`main.py` constructs the `WebApp` and attaches the router:

```python
import htpy as y
from pyhx.core import WebApp

from .pages import users

app = WebApp(title="My App")
app.include_router(users.router)

@app.page("/", title="Home")
async def home() -> y.Node:
    return y.div[
        y.h1["Home"],
        y.a(href=users.users_page.url())["Users"],
    ]

fastapi_app = app.create_app()
```

Both `@app.page(...)` (used in `main.py`) and `@router.page(...)` (used in `pages/users.py`) produce `Page` objects with the same surface, so `users.users_page.url()` and `nav_item(users.users_page)` work exactly like they would for a directly-declared page.

## What goes on a router

`WebAppRouter` mirrors the parts of `WebApp` that declare routes:

| Router attribute | Equivalent on `WebApp` | Purpose |
| --- | --- | --- |
| `router.page(path, *, title, icon=None)` | `app.page(...)` | Decorate a page handler |
| `router.fragment.get/post/put/patch/delete(path)` | `app.fragment.<verb>(...)` | Decorate a fragment handler |
| `router.add_websocket(ws)` | `WebApp(websockets=[...])` | Register a websocket instance |

A router does **not** carry navigation, the default page template, or static directories — those are app-level concerns and stay on the `WebApp`.

## `include_router(router, prefix="")`

Attaches every captured page, fragment, and websocket to the app, optionally prepending a URL prefix:

```python
app.include_router(users.router)                       # mounts at /users, /users/{user_id}
app.include_router(admin.router, prefix="/admin")      # mounts at /admin/<every captured path>
```

When a prefix is given, the **handle's path is rewritten in place**. That means `users.users_page.url()` returns the prefixed URL (`/admin/users` in the second call above), and `nav_item(users.users_page)` builds correct links — no extra bookkeeping needed.

### Rules

- A `WebAppRouter` can be included **at most once**. Including it twice raises `RuntimeError`. To use the same routes under two prefixes, construct two routers (e.g. by factoring router-construction into a function and calling it twice).
- `prefix` must either be empty (or `"/"`, which is equivalent) or start with `"/"`. Trailing slashes are stripped — `"/admin/"` and `"/admin"` are the same.
- The prefix is concatenated *before* every captured path. There's no per-route override.

## When to use a router vs the `WebApp` decorator

- **Single-file app, no plans to split:** use `@app.page(...)` directly. The router adds boilerplate without benefit.
- **App that already lives across multiple modules:** use a router per module. The page module never imports the live `WebApp`, so there are no circular-import pressures and the file is independently testable.
- **A feature you want to mount under different paths in different apps** (e.g. `/admin/users` in one app, `/dashboard/users` in another): build the router behind a function and call it for each app — each call returns a fresh router that's included once.

## Fragments and components — separate mechanism

Fragments declared via `@hx.fragment.<verb>(...)` (module-level) or on a `@component` continue to use the **global fragment registry**. They're attached to *every* `WebApp` constructed in the process via the registry's replay-on-subscribe mechanism, and they do not require a router. The two systems coexist:

- **Router fragments** (`router.fragment.<verb>(...)`) — explicitly scoped to a router, registered with the apps that include the router. Use this for fragments that belong to a feature module.
- **Global / component fragments** — globally registered at import time, picked up by every `WebApp`. Use this for fragments that ship with a reusable component.

See [Components](../concepts/components.md) and [Fragments & HTMX](../concepts/fragments.md#module-level-fragments-with-hx) for the global path.

## Sample layout

The `samples/components/` and `samples/app_shell_layout/` directories in the repo use this exact pattern:

```
samples/components/
    main.py                     # WebApp + home + nav + create_app
    pages/
        __init__.py
        pills.py                # router + pills_page
        buttons.py              # router + buttons_page
        grid.py                 # router + grid_page
```

Each page module imports `WebAppRouter` from `pyhx.core`, declares its routes on a local `router`, and exports the page handle(s) so the top-level navigation and home page can link to them.

## Caveat: package boundaries with `fastapi dev`

`fastapi dev <path>` walks the filesystem up from the entry-point file looking for `__init__.py` markers to determine the parent package, then imports the module by its dotted path. For relative imports (`from .pages import ...`) inside the entry point to work, every directory between the entry point and the project root must contain an `__init__.py` (and the directory names must be valid Python identifiers — no dashes). Without those markers, fastapi_cli adds the immediate parent to `sys.path` and imports the file as a top-level module, breaking relative imports.
