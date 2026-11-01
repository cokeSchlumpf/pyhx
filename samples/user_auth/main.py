"""User authentication sample, multilingual.

Run with::

    poetry run fastapi dev samples/user_auth/main.py

Exercises :func:`configure_user_authentication` — the addon registers
``GET``/``POST`` ``/login`` and ``GET`` ``/logout`` against an in-memory
:class:`SQLUsersRepository` seeded with two test accounts:

- ``jane`` / ``pw`` (``jane@example.com``), who never chose a language,
- ``marco`` / ``pw`` (``marco@example.com``), whose stored language is Italian.

The login page offers both login methods: username and password, and a
link and code sent by email. The sample uses the default
``LoggingLoginTokenSender``, so the link and the code appear in the console
instead of an inbox.

The home page renders the current viewer (real or :class:`AnonymousUser`).
``/protected`` calls :func:`require_authenticated_user`, which redirects
anonymous visitors to ``/login?next=/protected``.

Languages (:mod:`pyhx.i18n`): the app offers en, de, it and fr. The language
of a request is the one chosen in the session, else the signed-in user's,
else the browser's, else English. Try it:

- As an anonymous visitor, switch the language in the settings menu (the gear
  in the header: ``settings=[account_links, LanguageSetting()]``; the account
  links, Profile and Sign out, appear once signed in): it is
  kept in the session only (open a private window: English or your browser's
  language again).
- Sign in as ``jane`` and switch: the language is also stored on the user, so
  it is back after signing out and in again, in a new browser.
- Sign in as ``marco`` in a new browser: the page is Italian without choosing.

The texts of the sample are marked with ``_``, ``_n`` and ``t`` and
translated in ``samples/user_auth/locale/`` (``WebApp(locale_dir=…)``); the
catalog also overrides one text of pyhx (the "Sign in" button of the login
page reads "Einloggen" in German instead of pyhx's "Anmelden"). Numbers,
dates and relative times use the format helpers of :mod:`pyhx.i18n`.

Note: sessions are kept in-process; restarting the server logs you out.
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import htpy as y
from commons.users import AnonymousUser, RegisteredUser, SQLUsersRepository
from sqlalchemy import create_engine

from pyhx.addons.user_authentication import (
    EmailTokenLogin,
    PasswordLogin,
    configure_user_authentication,
    require_authenticated_user,
    require_user,
)
from pyhx.core import WebApp
from pyhx.i18n import (
    _,
    _l,
    _n,
    format_currency,
    format_date,
    format_number,
    format_relative_time,
    t,
)
from pyhx.page_templates import AppShell, LanguageSetting, SettingsLink, SettingsLinks

LOCALE_DIR = Path(__file__).parent / "locale"


def _build_users_repo() -> SQLUsersRepository:
    # A fresh SQLite file per start, not `:memory:` + StaticPool: the session
    # middleware looks the user up in worker threads, in parallel for the
    # page's assets, and a single shared connection can't serve that.
    path = Path(tempfile.mkdtemp(prefix="pyhx-user-auth-")) / "users.db"
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}
    )
    repo = SQLUsersRepository(engine)
    repo.upsert_user(
        RegisteredUser.create(
            username="jane",
            password_hash=repo.hash_password("pw"),
            display_name="Jane Doe",
            email="jane@example.com",
        )
    )
    repo.upsert_user(
        RegisteredUser.create(
            username="marco",
            password_hash=repo.hash_password("pw"),
            display_name="Marco Rossi",
            email="marco@example.com",
            locale="it",
        )
    )
    return repo


users = _build_users_repo()


def account_links() -> y.Node:
    """Settings entry of the sample: profile and sign-out, for signed-in users only."""
    if isinstance(require_user(), AnonymousUser):
        return None
    return SettingsLinks(
        SettingsLink(_l("Profile"), "/profile", icon="user"),
        SettingsLink(_l("Sign out"), "/logout", icon="log-out"),
    )()


# The settings menu (gear in the header): account links above the language.
SETTINGS = [account_links, LanguageSetting()]

hx = WebApp(
    title="User Auth Sample",
    default_page_template=AppShell(
        mode="app", main_navigation=False, user_menu=False, settings=SETTINGS
    ),
    locale_dir=LOCALE_DIR,
)


configure_user_authentication(
    hx,
    users=users,
    login_methods=[PasswordLogin(), EmailTokenLogin()],
    secret_key="dev-only-sample-key-do-not-use-in-prod",
    https_only=False,
)


# Example data for the formatting table: (case, amount in EUR, opened how long ago).
_CASES = [
    ("A-1042", 1234.5, timedelta(hours=3)),
    ("B-2001", 98000, timedelta(days=12)),
    ("C-0007", 12.75, timedelta(minutes=5)),
]


def _formatting_table() -> y.Node:
    now = datetime.now(UTC)
    return y.table[
        y.thead[
            y.tr[
                y.th[_("Case")],
                y.th[_("Amount")],
                y.th[_("Opened")],
                y.th[_("Since")],
            ]
        ],
        y.tbody[
            (
                y.tr[
                    y.td[name],
                    y.td[format_currency(amount, "EUR")],
                    y.td[format_date(now - ago, "long")],
                    y.td[format_relative_time(now - ago, now=now)],
                ]
                for name, amount, ago in _CASES
            )
        ],
    ]


@hx.page("/", title=_l("Home"))
async def home() -> y.Node:
    user = require_user()
    is_anonymous = user is None or isinstance(user, AnonymousUser)
    return y.main[
        y.article[
            y.h1[_("User authentication sample")],
            y.p[
                t(
                    "Sign in as {jane} or {marco} (password {password}), or with {email} — the login link and code appear in the console.",
                    jane=y.code["jane"],
                    marco=y.code["marco"],
                    password=y.code["pw"],
                    email=y.code["jane@example.com"],
                )
            ],
            y.p[y.em[_("You are not signed in.")]]
            if is_anonymous
            else y.p[t("Signed in as {name}.", name=y.strong[user.display_name])],
            y.p[
                _n(
                    "There is {n} open case worth {total}.",
                    "There are {n} open cases worth {total}.",
                    len(_CASES),
                    total=format_number(sum(amount for _c, amount, _o in _CASES)),
                )
            ],
            _formatting_table(),
            y.ul[
                y.li[y.a(href=protected.url())[_("Visit the protected page")]],
                y.li[y.a(href="/login")[_("Sign in")]]
                if is_anonymous
                else y.li[y.a(href="/logout")[_("Sign out")]],
            ],
        ],
    ]


@hx.page("/protected", title=_l("Protected"))
async def protected() -> y.Node:
    user = require_authenticated_user()
    return y.main[
        y.article[
            y.h1[_("Protected")],
            y.p[t("You're signed in as {name}.", name=y.strong[user.display_name])],
            y.p[
                y.a(href="/")[_("Home")],
                " · ",
                y.a(href="/logout")[_("Sign out")],
            ],
        ],
    ]


@hx.page("/profile", title=_l("Profile"))
async def profile() -> y.Node:
    user = require_authenticated_user()
    stored = getattr(user, "locale", None)
    return y.main[
        y.article[
            y.h1[_("Profile")],
            y.dl[
                y.dt[_("Name")],
                y.dd[user.display_name],
                y.dt[_("Stored language")],
                y.dd[stored or _("none (the browser's language applies)")],
            ],
            y.p[y.a(href="/")[_("Home")]],
        ],
    ]


app = hx.create_app()
