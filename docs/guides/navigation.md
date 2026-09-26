# Navigation

PyHX's navigation system is a small set of primitives — `NavItem`, `Nav`, and the `NavFactory` decorator — designed to let your layout render navigation that reflects the current request.

## `NavItem`

A `NavItem` is a single navigation entry: a label, a target, and an active-state rule.

```python
from pyhx.core import NavItem

NavItem(label="Home", to="/", full_match=True)
NavItem(label="Users", to="/users", full_match=False)
```

- `to` may be a `str` or a `Path`.
- `full_match=True` (the default) means the item is active only on an exact path match.
- `full_match=False` activates the item whenever its `to` is a prefix of the current path — useful for section roots like `/users` that should highlight on `/users/42`, `/users/42/posts`, etc.

## `nav_item(...)` helper

Most navigation entries point to pages you've already declared. `nav_item` has two overloads to make that ergonomic:

```python
from pyhx.core import nav_item

# 1. From a Page — label defaults to page.title.
nav_item(home_page)
nav_item(user_page, params={"user_id": 42})
nav_item(home_page, label="Dashboard", full_match=True)

# 2. From a label + target.
nav_item("External docs", to="/docs", full_match=False)
```

When passed a `Page`, `nav_item` calls `page.path.format(**params)` to produce the `to` URL, so parameterized pages are easy to link to.

## `Nav`

A `Nav` is either a flat list of items, or a dict mapping slot names to lists:

```python
Nav = list[NavItem] | dict[str, list[NavItem]]
```

Use a `dict` when your layout has more than one navigation region (e.g. a main sidebar and a secondary footer). Slot keys are arbitrary strings agreed between your layout and your nav factory.

## Registering navigation with a `WebApp`

Navigation is registered through the `@app.navigation(slot)` decorator. The decorated function is `async`, receives the current `RequestContext`, and returns a `Nav`:

```python
from pyhx.core import RequestContext, nav_item

@app.page("/", title="Home")
async def home(): ...

@app.page("/users", title="Users")
async def users(): ...

@app.navigation("main")
async def main_nav(ctx: RequestContext):
    return [
        nav_item(home, full_match=True),
        nav_item(users),
    ]
```

The default page template (`Skeleton`) renders the `"main"` slot. Custom templates can read any slots they need from the `navigation` argument they receive — see [Layouts & Templates](layouts.md).

## Active-state detection

`NavItem.is_active(ctx)` inspects the request URL on `ctx.request` and returns `True` when the item should be highlighted, applying the `full_match` rule. Your template uses this to decide whether to add an `"active"` class, change the color, etc.

This means nav items are recomputed per request, which is what makes section-based active states (`/users/42` highlights the "Users" item) work without any client-side code.
