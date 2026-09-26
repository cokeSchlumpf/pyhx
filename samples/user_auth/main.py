"""User authentication sample.

Run with::

    poetry run fastapi dev samples/user_auth/main.py

Exercises :func:`configure_user_authentication` — the addon registers
``GET``/``POST`` ``/login`` and ``GET`` ``/logout`` against an in-memory
:class:`SQLUsersRepository` seeded with a test account (``jane`` / ``pw``).

The home page uses :func:`get_user` to render the current viewer (real
or :class:`AnonymousUser`). ``/protected`` calls
:func:`require_user`, which raises
:class:`NotAuthenticated` for anonymous visitors; the addon's exception
handler then redirects to ``/login?next=/protected`` so the post-login
flow lands them back where they came from.

Note: sessions are kept in-process; restarting the server logs you out.
"""

import htpy as y
from commons.users import AnonymousUser, RegisteredUser, SQLUsersRepository
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from pyhx.addons.user_authentication import (
    configure_user_authentication,
    require_authenticated_user,
    require_user
)
from pyhx.core import WebApp
from pyhx.page_templates import AppShell


def _build_users_repo() -> SQLUsersRepository:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repo = SQLUsersRepository(engine)
    repo.upsert_user(
        RegisteredUser.create(
            username="jane",
            password_hash=repo.hash_password("pw"),
            display_name="Jane Doe",
        )
    )
    return repo


users = _build_users_repo()


hx = WebApp(
    title="User Auth Sample", 
    default_page_template=AppShell(mode="app", main_navigation=False, user_menu=False)
)


configure_user_authentication(
    hx,
    users=users,
    secret_key="dev-only-sample-key-do-not-use-in-prod",
    https_only=False,
)


@hx.page("/", title="Home")
async def home() -> y.Node:
    user = require_user()
    is_anonymous = user is None or isinstance(user, AnonymousUser)
    return y.main[
        y.article[
            y.h1["User authentication sample"],
            y.p[
                "Sign in as ",
                y.code["jane"],
                " / ",
                y.code["pw"],
                ".",
            ],
            y.p[y.em["You are not signed in."]]
            if is_anonymous
            else y.p["Signed in as ", y.strong[user.display_name], "."],
            y.ul[
                y.li[y.a(href=protected.url())["Visit /protected"]],
                y.li[y.a(href="/login")["Go to /login"]]
                if is_anonymous
                else y.li[y.a(href="/logout")["Sign out"]],
            ],
        ],
    ]


@hx.page("/protected", title="Protected")
async def protected() -> y.Node:
    user = require_authenticated_user()
    return y.main[
        y.article[
            y.h1["Protected"],
            y.p[
                "You're signed in as ",
                y.strong[user.display_name],
                ".",
            ],
            y.p[y.a(href="/")["Home"], " · ", y.a(href="/logout")["Sign out"]],
        ],
    ]


app = hx.create_app()
