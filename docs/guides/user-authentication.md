# User Authentication

The `pyhx.addons.user_authentication` addon wires a cookie-backed sign-in flow onto a `WebApp` in one call: session middleware, default `/login` and `/logout` pages, and a `NotAuthenticated` exception that handlers can raise to redirect anonymous viewers to the login page. Any of the three can be turned off independently.

User identity is sourced from a [`UsersRepository`](https://pypi.org/project/kpmg-commons-users/) — the example below uses the in-memory SQLite implementation.

## Quick start

```python
import htpy as y
from commons.users import RegisteredUser, SQLUsersRepository
from sqlalchemy import create_engine

from pyhx.addons.user_authentication import (
    configure_user_authentication,
    require_authenticated_user,
)
from pyhx.core import WebApp


users = SQLUsersRepository(create_engine("sqlite:///app.db"))
users.upsert_user(
    RegisteredUser.create(
        username="jane",
        password_hash=users.hash_password("pw"),
        display_name="Jane Doe",
    )
)

app = WebApp(title="My App")
configure_user_authentication(app, users=users)


@app.page("/protected", title="Protected")
async def protected() -> y.Node:
    user = require_authenticated_user()
    return y.div[y.h1[f"Hello, {user.display_name}"]]


fastapi_app = app.create_app()
```

Out of the box:

- `GET /login` renders a username/password form.
- `POST` to the form's submit endpoint authenticates against `users.authenticate(...)`. On success the session cookie is set and the browser navigates to `/` (or to a safe `?next=` URL); on failure the form re-renders with an inline notification.
- `GET /logout` clears the session and redirects to `/login`.
- Any handler that raises `NotAuthenticated` is redirected to `/login?next=<original-url>`.

## Gating handlers

Three accessors read the current user out of `RequestContext`. They never have to be wired into the handler signature — call them directly from inside the handler body.

| Accessor | Returns | Raises |
| --- | --- | --- |
| `require_user()` | `User` (anonymous *or* signed in) | — |
| `require_authenticated_user()` | `AuthenticatedUser | RegisteredUser` | `NotAuthenticated` for anonymous viewers |
| `require_registered_user()` | `RegisteredUser` | `NotAuthenticated` for anonymous *and* externally authenticated users |

`require_user` is for handlers that show different content to anonymous and signed-in viewers (e.g. a public home page). The other two are gates — they raise `NotAuthenticated`, which the addon's exception handler converts into the right kind of redirect for the request:

- Plain request → `303 See Other` with `Location: /login?next=<current url>`.
- HTMX request (`HX-Request: true`) → `200 OK` with `HX-Redirect: /login?next=<current url>`. HTMX swallows 3xx redirects via XHR and would otherwise swap the login page's HTML into the form's wrapper, so the addon picks the response shape that triggers a real browser navigation.

```python
@app.page("/dashboard", title="Dashboard")
async def dashboard() -> y.Node:
    user = require_authenticated_user()      # redirects anonymous to /login
    return y.div[f"Welcome back, {user.display_name}"]


@app.page("/", title="Home")
async def home() -> y.Node:
    user = require_user()                    # never raises
    if isinstance(user, AnonymousUser):
        return y.p["Please ", y.a(href="/login")["sign in"], "."]
    return y.p[f"Signed in as {user.display_name}"]
```

Calling these from a non-request context (background tasks, scripts) raises `LookupError` from the underlying `RequestContext.get()`.

## Session settings

Every knob that shapes the session cookie is exposed both as a kwarg on `configure_user_authentication(...)` and as a `[app.pyhx]` settings field. Each kwarg defaults to `None`; when left at `None` the addon falls back to the settings value. Pass an explicit value to override settings without touching config — typical for tests, scripts, or apps with their own config mechanism.

```toml
# pyproject.toml, settings.toml, or ~/.kpmg_apps/settings.toml
[app.pyhx]
sessions_secret_key  = "<32+ random bytes — hex or base64>"
sessions_cookie_name = "pyhx_session"
sessions_max_age     = 1209600          # 14 days, in seconds
sessions_same_site   = "lax"            # "lax" | "strict" | "none"
sessions_https_only  = false            # set true in prod
sessions_domain      = ""               # empty = no Domain restriction
sessions_path        = "/"
```

Each field has a matching env var: `APP__PYHX__SESSIONS_SECRET_KEY`, `APP__PYHX__SESSIONS_HTTPS_ONLY`, etc.

### Defaults

| Setting | Default | Maps to (kwarg / Starlette) |
| --- | --- | --- |
| `sessions_secret_key` | — (required) | `secret_key` |
| `sessions_cookie_name` | `"pyhx_session"` | `session_cookie` |
| `sessions_max_age` | 14 days | `max_age` |
| `sessions_same_site` | `"lax"` | `same_site` |
| `sessions_https_only` | `false` | `https_only` |
| `sessions_domain` | `null` (no `Domain` attribute) | `domain` |
| `sessions_path` | `"/"` | `path` |

The defaults are dev-friendly: HTTP-safe (`sessions_https_only = false`) and unscoped (no `Domain`). Flip `sessions_https_only` to `true` for any prod deployment served over HTTPS.

### The secret key — special case

If `sessions_secret_key` is missing (or left at the placeholder `"xxx"`) the addon's behaviour depends on `WebApp.is_dev`:

- **Dev mode** — a random per-process key is generated and a warning is logged. Sessions don't survive a restart and aren't shared across workers, but the addon stays usable without any config.
- **Prod mode** — startup raises `RuntimeError`. Refusing to start prevents silently signing real sessions with a key that vanishes on the next deploy.

### "None means settings" — caveat

Because every cookie kwarg defaults to `None` and falls back to settings, callers cannot force a value *back* to `None` (e.g. clearing `domain` when settings set it). Set the override explicitly via TOML / env in that case instead.

## Customising paths and redirects

```python
configure_user_authentication(
    app,
    users=users,
    login_path="/sign-in",
    logout_path="/sign-out",
    post_login_redirect="/dashboard",
    post_logout_redirect="/sign-in",
)
```

`post_login_redirect` is the fallback after a successful login when no `?next=` was supplied. A `?next=` value is only honoured if it's a same-origin path (starts with a single `/`); protocol-relative URLs (`//evil.example`), absolute URLs (`https://...`), and `javascript:` are silently dropped to the fallback.

## Bringing your own login UI

Skip the bundled pages but keep everything else:

```python
configure_user_authentication(
    app,
    users=users,
    include_default_pages=False,
    login_path="/my-login",          # must point at your own page
)


@app.page("/my-login", title="Sign in")
async def my_login() -> y.Node:
    return y.div[...]                # your own form
```

The `NotAuthenticated` exception handler is registered **independently** of `include_default_pages`. As long as you set `login_path` to whatever URL your own login page lives at, `require_authenticated_user()` / `require_registered_user()` keep redirecting correctly. Forgetting to align them lands the redirect on a 404.

To skip the exception handler too, pass `include_exception_handler=False`.

## Just the session, no pages, no handler

`configure_user_session(...)` wires only `SessionMiddleware` + `CookieUserSession`. Use it when you need the session layer but want to compose everything else yourself:

```python
from pyhx.addons.user_authentication import (
    configure_user_session,
    login_user,
    logout_user,
)
```

`login_user(request, user)` and `logout_user(request)` are the low-level primitives that the default pages use under the hood. They work against any object exposing `.session` — both `Request` and `WebSocket`.

## Full reference

| Symbol | Purpose |
| --- | --- |
| `configure_user_authentication(app, users=, ...)` | All-in-one wiring: session middleware + default pages + exception handler |
| `configure_user_session(app, users=, ...)` | Just the session layer |
| `login_user(connection, user)` | Mark the connection's session as belonging to `user` |
| `logout_user(connection)` | Clear the user from the session |
| `require_user() -> User` | Current user from `RequestContext`, anonymous included |
| `require_authenticated_user() -> AuthenticatedUser \| RegisteredUser` | Raises `NotAuthenticated` for anonymous |
| `require_registered_user() -> RegisteredUser` | Raises `NotAuthenticated` for anonymous and externally authenticated |
| `NotAuthenticated` | Exception that the addon's handler turns into a login redirect |
| `CookieUserSession` | The ASGI middleware that resolves the user from the cookie |
| `UserSessionSettings` | The settings object backing `sessions_secret_key` |

Working sample app: `samples/user_auth/main.py` (`poetry run fastapi dev samples/user_auth/main.py`).
