"""User authentication sample in the canvas design.

Run with::

    poetry run fastapi dev samples/user_auth/canvas.py

Same accounts and login methods as ``main.py``, but the app uses
``CanvasShell``: the login pages follow the app's default page template, so
the user signs in on the canvas. ``/login`` starts with the list of login
methods (``default_login_method=None``); ``main.py`` starts with the first
method. The login link and code appear in the
console (``LoggingLoginTokenSender``).

The settings menu (the gear in the top bar) switches the language, also on
the login pages; texts and catalogs are shared with ``main.py``.
"""

import htpy as y

import pyhx.components as c
from pyhx.addons.user_authentication import (
    EmailTokenLogin,
    PasswordLogin,
    configure_user_authentication,
    require_authenticated_user,
)
from pyhx.core import WebApp
from pyhx.i18n import _, _l, t
from pyhx.page_templates import CanvasShell
from samples.user_auth.main import LOCALE_DIR, SETTINGS, _build_users_repo

hx = WebApp(
    title="User Auth Canvas",
    default_page_template=CanvasShell(settings=SETTINGS),
    locale_dir=LOCALE_DIR,
)

configure_user_authentication(
    hx,
    users=_build_users_repo(),
    login_methods=[PasswordLogin(), EmailTokenLogin()],
    default_login_method=None,  # start with the list of login methods
    secret_key="dev-only-sample-key-do-not-use-in-prod",
    https_only=False,
)


@hx.page("/", title=_l("Home"))
async def home() -> y.Node:
    user = require_authenticated_user()
    return c.card[
        c.card.header[c.card.title[y.h1[_("Signed in")]]],
        c.card.section[
            y.p[t("You're signed in as {name}.", name=y.strong[user.display_name])],
            y.p[y.a(href="/logout")[_("Sign out")]],
        ],
    ]


@hx.page("/profile", title=_l("Profile"))
async def profile() -> y.Node:
    user = require_authenticated_user()
    return c.card[
        c.card.header[c.card.title[y.h1[_("Profile")]]],
        c.card.section[
            y.p[t("You're signed in as {name}.", name=y.strong[user.display_name])],
            y.p[_("Stored language"), ": ", getattr(user, "locale", None) or "–"],
            y.p[y.a(href="/")[_("Home")]],
        ],
    ]


app = hx.create_app()
