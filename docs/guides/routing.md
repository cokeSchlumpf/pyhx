# Routing & Paths

PyHX uses two related primitives for URL paths:

- **`PathTemplate`** — a path with named variables, e.g. `"/users/{user_id}/posts/{post_id}"`.
- **`Path`** — a concrete, fully-expanded path, e.g. `"/users/42/posts/abc"`.

Both are imported from `pyhx.core.primitives` when you need them directly. Day-to-day you'll mostly pass plain strings to the page and fragment decorators, and PyHX will parse them into `PathTemplate`s for you.

## Syntax

Inspired by [RFC 6570](https://datatracker.ietf.org/doc/html/rfc6570) templates, but deliberately restricted:

- Static segments: `[a-z0-9_-]+` (lowercase letters, digits, underscore, hyphen)
- Variable segments: `{name}` where `name` matches `[a-z][a-z0-9_]*`
- No trailing slash, except for the root path `/`
- Variable names must be unique within a template

```python
"/users"                          # OK
"/users/{user_id}"                # OK
"/users/{user_id}/posts/{post_id}"  # OK
"/"                               # OK (root)
"/Users"                          # INVALID — uppercase
"/users/"                         # INVALID — trailing slash
"/users/{id}/posts/{id}"          # INVALID — duplicate variable
```

Invalid templates raise `ValueError` at parse time, so you get the error at app startup rather than on first request.

## `PathTemplate`

```python
from pyhx.core.primitives import PathTemplate

t = PathTemplate("/users/{user_id}/posts/{post_id}")
t.expand(user_id=42, post_id="abc")
# -> Path("/users/42/posts/abc")

t.match("/users/42/posts/abc")
# -> {"user_id": "42", "post_id": "abc"}

t.match("/users/42")
# -> None
```

`expand(**values)` (also available as `format(**values)`) substitutes variables into the template and returns a concrete `Path`. Missing or unexpected variables raise `ValueError`.

`match(path)` returns the captured variables as a `dict` if the path matches, or `None` if it doesn't.

`is_parameterized()` returns `True` if the template has any variables.

## `Path`

`Path` represents a fully-expanded URL path. It's used internally for matching, navigation active-state checks, and anywhere a concrete path is needed:

```python
from pyhx.core.primitives import Path

p = Path("/users/42")
p.is_prefix_of(Path("/users/42/posts"))   # True
p.is_prefix_of(Path("/users/42-admin"))   # False — segment-based
```

`is_prefix_of` compares whole path segments, so `/users` is **not** a prefix of `/users-admin`.

## Joining paths

Both `PathTemplate` and `Path` support `join` and the `/` operator:

```python
PathTemplate("/api") / PathTemplate("/users/{id}")
# -> PathTemplate("/api/users/{id}")

Path("/api") / Path("/v1") / PathTemplate("/users/{id}")
# -> PathTemplate("/api/v1/users/{id}")
```

Joining widens the result to a `PathTemplate` whenever either side is parameterized.

## Page URL helpers

A `Page` exposes a `url(**params)` shortcut that delegates to its template's `expand`:

```python
@app.page("/users/{user_id}", title="User")
async def user(user_id: str) -> y.Node: ...

# elsewhere:
user.url(user_id=42)   # -> "/users/42"
```

This is the idiomatic way to build links and `hx_*` URLs without hard-coding paths.
