"""Login methods an app offers on its login page.

Passed to :func:`configure_user_authentication` as ``login_methods``. Each
method has its own login page (``/login?method=<key>``); with more than one
method, ``/login?method=select`` lists them, in the given order.
"""

from dataclasses import dataclass
from typing import ClassVar, cast

from commons.users.login_tokens import (
    LoginTokenSettings,
    LoginTokenStore,
    SendLoginTokenPort,
)

from pyhx.core.primitives import IconName
from pyhx.i18n import _l


@dataclass(frozen=True)
class LoginMethod:
    """Base class of the login methods for
    ``configure_user_authentication(login_methods=...)``.

    ``key`` identifies the method in ``/login?method=…``; label, description
    and icon show on the page that lists the methods. Label and description
    may be marked with ``_l`` to show in the language of the request.
    """

    key: ClassVar[str]
    label: ClassVar[str]
    description: ClassVar[str]
    icon: ClassVar[IconName]


@dataclass(frozen=True)
class PasswordLogin(LoginMethod):
    """Username and password, checked by ``UsersRepository.authenticate``.

    The default login method.
    """

    key: ClassVar[str] = "password"
    label: ClassVar[str] = cast(str, _l("Username and password"))
    description: ClassVar[str] = cast(
        str, _l("Sign in with your username and password.")
    )
    icon: ClassVar[IconName] = "lock"


@dataclass(frozen=True)
class EmailTokenLogin(LoginMethod):
    """Login with a link or code sent to a registered user's email address.

    The user enters their address; a link and a code are sent via
    ``sender``. Opening the link logs in on any device; the code is typed
    into the browser that requested it. Both are single use and expire
    (``app.login_tokens.token_ttl``, 15 minutes by default). Built on
    :mod:`commons.users.login_tokens`; hashes are keyed with the session's
    secret key.

    Attributes:
        store: Where login requests are kept. Defaults to an
            ``InMemoryLoginTokenStore`` — fine for a single process; with
            several workers use ``SQLLoginTokenStore``, or a link sent by
            one worker won't work on another.
        sender: Delivers link and code. Defaults to
            ``LoggingLoginTokenSender``, which writes them to the log
            (development only).
        settings: Validity, code length and rate limit. Defaults to
            ``LoginTokenSettings.read()`` (``app.login_tokens.*``).
        base_url: Absolute base URL for the links in the email, e.g.
            ``"https://app.example.com"``. Defaults to the public URL of the
            app (``app.public_url`` of ``commons.settings.AppSettings``, set
            by the deployment as ``APP__PUBLIC_URL``), else to the URL the
            request came in on, which is wrong behind a proxy that rewrites
            the host.
    """

    key: ClassVar[str] = "email"
    label: ClassVar[str] = cast(str, _l("Email"))
    description: ClassVar[str] = cast(str, _l("Get a login link and a code by email."))
    icon: ClassVar[IconName] = "mail"

    store: LoginTokenStore | None = None
    sender: SendLoginTokenPort | None = None
    settings: LoginTokenSettings | None = None
    base_url: str | None = None
