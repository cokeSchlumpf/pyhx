# Components

A **component** is a reusable HTML-producing function with its own private fragment routes. Components let you bundle a piece of UI together with the HTMX endpoints that power it, so callers can drop in the component and the routes come along for free.

## Declaring a component

```python
import htpy as y
from pyhx.core import component

@component
def greeting(name: str) -> y.Node:
    return y.div(cls="greeting")[
        y.h2[f"Hello, {name}"],
    ]
```

`@component` wraps the function so it can still be called directly (`greeting("World")`) and gains a `fragments` attribute for declaring HTMX endpoints scoped to this component.

## Adding fragments to a component

```python
@component
def counter(start: int = 0) -> y.Node:
    return y.div[
        y.span(id="count")[str(start)],
        y.button(
            hx_post="/_components/counter/increment",
            hx_target="#count",
            hx_swap="innerHTML",
        )["+1"],
    ]

@counter.fragments.post("/increment")
async def increment() -> y.Node:
    # Stateful counters need real storage; this is illustrative.
    return y.span["1"]
```

Fragments declared via `<component>.fragments.<verb>(path)` are mounted under `/_components/<function-name>/<path>`. The component above exposes `POST /_components/counter/increment`.

Like the top-level fragment factory, `component.fragments` supports `get`, `post`, `put`, `patch`, and `delete`.

## Auto-registration

By default, `@component` registers its fragments with the process-global fragment registry as soon as the module containing them is imported. When you later construct a `WebApp`, it picks up all registered component fragments automatically — you don't have to enumerate them.

If you want to opt out (e.g. for tests, or for components you build but don't always serve), pass `auto_register=False`:

```python
@component(auto_register=False)
def widget() -> y.Node:
    return y.div["…"]
```

You can then attach the component's fragments to a specific `WebApp` manually.

## When to reach for a component vs a fragment

- **Fragment** when you have a single endpoint that returns HTML for an existing page.
- **Component** when you want a self-contained UI piece (markup + one or more fragments) that you'll instantiate in multiple places, or whose internal endpoints you want grouped under a stable prefix.
