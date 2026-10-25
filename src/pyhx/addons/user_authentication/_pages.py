"""Default login and logout pages plus their form models.

Registered by :func:`configure_user_authentication` when
``include_default_pages=True`` (the default). The login page renders one
form per configured login method (:mod:`._methods`).

Email login adds three pages below ``login_path``:

- ``{login_path}/code`` — "we've sent you an email", with a field for the
  code. The id of the pending request lives in the session, so the code
  only works in the browser that requested it.
- ``{login_path}/token?t=…`` — the link from the email. Opened in the
  requesting browser (its session holds the matching request id), it logs
  in right away; anywhere else it shows a confirmation button, because
  mail scanners open links in advance — but never with that session.

Every failure shows the same neutral message, so the pages don't reveal
whether an address is registered.
"""

import asyncio
import logging
from typing import Annotated
from urllib.parse import urlencode

import htpy as y
from commons.users import RegisteredUser, UsersRepository
from commons.users.login_tokens import InMemoryLoginTokenStore, LoginTokenService
from fastapi import Query, Request
from pydantic import BaseModel

import pyhx.components as c
from pyhx.core import (
    FragmentResponse,
    PageResponse,
    PageTemplate,
    RequestContext,
    WebApp,
)
from pyhx.core.primitives import htmx
from pyhx.page_templates import AppShell

from ._methods import EmailTokenLogin, LoginMethod
from ._session import login_user, logout_user

LOG = logging.getLogger(__package__)

# Id of the email login request this browser is waiting for.
SESSION_LOGIN_REQUEST_KEY = "login_request_id"

# ``?method=`` value of the page that lists the login methods.
SELECT_METHOD = "select"

_CODE_FAILED = (
    "The code is invalid or has expired. Please check it or request a new one."
)
_LINK_FAILED = "This login link is invalid or has expired. Please request a new one."
_SEND_FAILED = "The email could not be sent. Please try again later."


@c.annotations.form(columns=1, submit_label="Sign In")
class LoginForm(BaseModel):
    username: Annotated[
        str,
        c.data.annotations.TextField(
            control=c.data.annotations.InputControl(), label="Username"
        ),
    ]
    password: Annotated[
        str,
        c.data.annotations.TextField(
            control=c.data.annotations.InputControl(type="password"), label="Password"
        ),
    ]
    next: Annotated[str | None, c.data.annotations.HiddenField()]


@c.annotations.form(columns=1, submit_label="Send login link")
class EmailLoginForm(BaseModel):
    email: Annotated[
        str,
        c.data.annotations.TextField(
            control=c.data.annotations.InputControl(type="email", autocomplete="email"),
            label="Email",
        ),
    ]
    next: Annotated[str | None, c.data.annotations.HiddenField()]


@c.annotations.form(columns=1, submit_label="Sign In")
class LoginCodeForm(BaseModel):
    code: Annotated[
        str,
        c.data.annotations.TextField(
            control=c.data.annotations.InputControl(
                inputmode="numeric", autocomplete="one-time-code"
            ),
            label="Code",
        ),
    ]


def _safe_next(value: str | None) -> str | None:
    """Return ``value`` only when it's safe to use as a post-login
    redirect target — a same-origin path starting with a single ``/``.

    Rejects protocol-relative URLs (``//evil.example``) and absolute
    URLs (``https://evil.example/...``) which would let an attacker
    bounce a freshly authenticated user off-site.
    """
    if not value or not value.startswith("/") or value.startswith("//"):
        return None
    return value


def _request() -> Request:
    request = RequestContext.get().request
    assert request is not None
    return request


def default_login_page_template(webapp: WebApp) -> PageTemplate:
    """The template of the login pages: the app's default template, so the
    login looks like the rest of the app (e.g. a ``CanvasShell`` app logs in
    on the canvas). An ``AppShell`` is replaced by one without navigation
    and user menu, which make no sense before signing in."""
    template = webapp.default_page_template
    if isinstance(template, AppShell):
        return AppShell(mode="app", main_navigation=False, user_menu=False)
    return template


def _login_box(*content: y.Node) -> y.Node:
    """The login column (``.hx-login``, centred by login.css); replaced
    out-of-band when a form is re-rendered."""
    return y.div(
        class_="hx-login",
        id="hx-login",
        **htmx(hx_swap_oob="#hx-login", as_dict=True),
    )[content]


def _card(title: y.Node, *body: y.Node, heading: y.Element = y.h1) -> y.Node:
    """One box of the login column. The first box of a page carries the
    page title (h1), further boxes an h2."""
    return c.card[
        c.card.header[c.card.title[heading[title]]],
        c.card.section[body],
    ]


def register_default_auth_pages(
    webapp: WebApp,
    *,
    users: UsersRepository,
    login_methods: list[LoginMethod],
    secret_key: str,
    login_page_template: PageTemplate,
    default_login_method: str | None,
    login_path: str,
    logout_path: str,
    post_login_redirect: str,
    post_logout_redirect: str,
) -> None:
    email_login = next(
        (m for m in login_methods if isinstance(m, EmailTokenLogin)), None
    )

    code_path = f"{login_path}/code"
    token_path = f"{login_path}/token"

    method_keys = [m.key for m in login_methods]
    several_methods = len(login_methods) > 1
    # The view of ``/login`` without ``?method``: the default method, or the
    # list of methods when there is no default (and more than one method).
    default_view = default_login_method or (
        SELECT_METHOD if several_methods else method_keys[0]
    )

    def method_url(method: str, next_: str = "") -> str:
        query = {"method": method} | ({"next": next_} if next_ else {})
        return f"{login_path}?{urlencode(query)}"

    def switch_link(next_: str) -> y.Node:
        """Subtle link from a method's page to the list of methods."""
        if not several_methods:
            return None
        return y.p(class_="hx-login__switch")[
            y.a(href=method_url(SELECT_METHOD, next_))["Sign in with another method"]
        ]

    def finish_login(user: RegisteredUser, next_: str | None) -> str:
        """Sign the user in and return where to go next."""
        request = _request()
        request.session.pop(SESSION_LOGIN_REQUEST_KEY, None)
        login_user(request, user)
        return _safe_next(next_) or post_login_redirect

    # --- Password ---------------------------------------------------------

    async def submit_login_form(form: LoginForm) -> y.Node | FragmentResponse:
        # bcrypt is deliberately slow: keep it off the event loop.
        user = await asyncio.to_thread(users.authenticate, form.username, form.password)

        if user is None:
            return y.fragment[
                await render_password_box(
                    next=form.next or "",
                    username=form.username,
                    password=form.password,
                ),
                c.notification(
                    "Invalid username or password.",
                    appearance="danger",
                    title="Login failed.",
                ),
            ]

        return FragmentResponse.redirect(finish_login(user, form.next))

    login_form = c.data.DataForm(
        name="app-login",
        routes=webapp,
        type=LoginForm,
        handle_submit=submit_login_form,
    )

    # --- Email: request a link and code -------------------------------------

    service: LoginTokenService | None = None
    if email_login is not None:
        service = LoginTokenService(
            users,
            email_login.store or InMemoryLoginTokenStore(),
            secret_key=secret_key,
            sender=email_login.sender,
            settings=email_login.settings,
        )

    async def submit_email_form(form: EmailLoginForm) -> y.Node | FragmentResponse:
        assert service is not None and email_login is not None
        request = _request()
        base_url = (email_login.base_url or str(request.base_url)).rstrip("/")

        def link_for(token: str) -> str:
            return f"{base_url}{token_path}?t={token}"

        try:
            result = await asyncio.to_thread(
                service.request_login,
                form.email,
                link_for=link_for,
                redirect_to=_safe_next(form.next),
            )
        except Exception:
            LOG.exception("Sending the login token failed.")
            return y.fragment[
                await render_email_box(next=form.next or "", email=form.email),
                c.notification(
                    _SEND_FAILED, appearance="danger", title="Login failed."
                ),
            ]

        # Whatever the status — sent, unknown address, rate limited — the
        # user lands on the same page.
        request.session[SESSION_LOGIN_REQUEST_KEY] = result.request_id
        return FragmentResponse.redirect(code_path)

    email_form = c.data.DataForm(
        name="app-login-email",
        routes=webapp,
        type=EmailLoginForm,
        handle_submit=submit_email_form,
    )

    # --- Email: enter the code ------------------------------------------------

    async def submit_code_form(form: LoginCodeForm) -> y.Node | FragmentResponse:
        assert service is not None
        request_id = _request().session.get(SESSION_LOGIN_REQUEST_KEY)
        if request_id:
            result = await asyncio.to_thread(service.redeem_code, request_id, form.code)
            if result.ok and result.user is not None:
                return FragmentResponse.redirect(
                    finish_login(result.user, result.redirect_to)
                )

        return y.fragment[
            await render_code_box(),
            c.notification(_CODE_FAILED, appearance="danger", title="Login failed."),
        ]

    code_form = c.data.DataForm(
        name="app-login-code",
        routes=webapp,
        type=LoginCodeForm,
        handle_submit=submit_code_form,
    )

    # --- Rendering ----------------------------------------------------------

    async def render_password_box(
        next: str, username: str = "", password: str = ""
    ) -> y.Node:
        return _login_box(
            _card(
                "Sign in",
                await login_form.render(
                    LoginForm(username=username, password=password, next=next)
                ),
            ),
            switch_link(next),
        )

    async def render_email_box(next: str, email: str = "") -> y.Node:
        return _login_box(
            _card(
                "Sign in",
                y.p[
                    "Enter your email address and we'll send you a login link ",
                    "and a code.",
                ],
                await email_form.render(EmailLoginForm(email=email, next=next)),
            ),
            switch_link(next),
        )

    def render_select_box(next: str) -> y.Node:
        return _login_box(
            c.card[
                c.card.header[
                    c.card.title[y.h1["Sign in"]],
                    c.card.subtitle["Choose how you want to sign in."],
                ],
                c.card.list[
                    [
                        c.card.item[
                            c.icon(method.icon, circle=True),
                            c.card.link(href=method_url(method.key, next))[
                                method.label
                            ],
                            c.card.subtle[method.description],
                            c.icon("arrow-right-2"),
                        ]
                        for method in login_methods
                    ]
                ],
            ]
        )

    async def render_view(view: str, next: str) -> y.Node:
        if view == SELECT_METHOD:
            return render_select_box(next)
        if view == EmailTokenLogin.key:
            return await render_email_box(next)
        return await render_password_box(next)

    async def render_code_box() -> y.Node:
        return _login_box(
            _card(
                "Check your email",
                y.p[
                    "If an account exists for this address, we've sent you a login ",
                    "link and a code. Open the link, or enter the code here.",
                ],
                await code_form.render(LoginCodeForm(code="")),
                y.p[y.a(href=method_url(EmailTokenLogin.key))["Request a new link"]],
            )
        )

    def message_box(title: str, text: str) -> y.Node:
        return _login_box(
            _card(title, y.p[text], y.p[y.a(href=login_path)["Back to sign in"]])
        )

    # --- Pages --------------------------------------------------------------

    @webapp.page(login_path, title="Sign in")
    async def login_page(
        next: Annotated[str, Query()] = "", method: Annotated[str, Query()] = ""
    ) -> PageResponse:
        if method in method_keys:
            view = method
        elif method == SELECT_METHOD and several_methods:
            view = SELECT_METHOD
        else:
            view = default_view
        return PageResponse(
            node=await render_view(view, next), page_template=login_page_template
        )

    if email_login is not None:

        @webapp.page(code_path, title="Check your email")
        async def code_page(request: Request) -> PageResponse:
            if not request.session.get(SESSION_LOGIN_REQUEST_KEY):
                return PageResponse.redirect(login_path)
            return PageResponse(
                node=await render_code_box(), page_template=login_page_template
            )

        @webapp.page(token_path, title="Sign in")
        async def token_page(
            request: Request, t: Annotated[str, Query()] = ""
        ) -> PageResponse:
            assert service is not None
            pending = request.session.get(SESSION_LOGIN_REQUEST_KEY)
            request_id = (
                await asyncio.to_thread(service.request_id_for_link, t) if t else None
            )

            if request_id is None:
                return PageResponse(
                    node=message_box("Login link not valid", _LINK_FAILED),
                    page_template=login_page_template,
                )

            # Opened in the browser that requested the link: log in right
            # away. A mail scanner never has this browser's session.
            if pending and pending == request_id:
                result = await asyncio.to_thread(service.redeem_link, t)
                if result.ok and result.user is not None:
                    return PageResponse.redirect(
                        finish_login(result.user, result.redirect_to)
                    )
                return PageResponse(
                    node=message_box("Login link not valid", _LINK_FAILED),
                    page_template=login_page_template,
                )

            return PageResponse(
                node=_login_box(
                    _card(
                        "Sign in",
                        y.p["Continue to sign in on this device."],
                        c.button(
                            "Sign In",
                            appearance="primary",
                            **htmx(hx_post=token_path, hx_vals={"t": t}),
                        ),
                    )
                ),
                page_template=login_page_template,
            )

        @webapp.fragment.post(token_path)
        async def redeem_token(request: Request) -> y.Node | FragmentResponse:
            assert service is not None
            token = str((await request.form()).get("t", ""))
            result = (
                await asyncio.to_thread(service.redeem_link, token) if token else None
            )
            if result is not None and result.ok and result.user is not None:
                return FragmentResponse.redirect(
                    finish_login(result.user, result.redirect_to)
                )
            return message_box("Login link not valid", _LINK_FAILED)

    @webapp.page(logout_path, title="Sign out")
    async def logout_handler(request: Request) -> PageResponse:
        logout_user(request)
        return PageResponse.redirect(post_logout_redirect)
