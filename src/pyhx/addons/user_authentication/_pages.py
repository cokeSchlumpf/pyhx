"""Default ``/login`` and ``/logout`` pages plus the ``LoginForm`` model.

Registered by :func:`configure_user_authentication` when
``include_default_pages=True`` (the default).
"""

from typing import Annotated

import htpy as y
from commons.users import UsersRepository
from fastapi import Query, Request
from pydantic import BaseModel

import pyhx.components as c
from pyhx.core import FragmentResponse, PageResponse, RequestContext, WebApp
from pyhx.core.primitives import htmx
from pyhx.page_templates import AppShell

from ._session import login_user, logout_user


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


def register_default_auth_pages(
    webapp: WebApp,
    *,
    users: UsersRepository,
    login_path: str,
    logout_path: str,
    post_login_redirect: str,
    post_logout_redirect: str,
) -> None:
    async def submit_login_form(form: LoginForm) -> y.Node | FragmentResponse:
        user = users.authenticate(form.username, form.password)

        if user is None:
            return y.fragment[
                await render_login_form(
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

        request = RequestContext.get().request
        assert request is not None
        login_user(request, user)
        return FragmentResponse.redirect(_safe_next(form.next) or post_login_redirect)

    async def render_login_form(
        next: str, username: str = "", password: str = ""
    ) -> y.Node:
        return y.div(
            class_="hx-login",
            id="hx-login",
            **htmx(hx_swap_oob="#hx-login", as_dict=True),
        )[
            y.article[
                await login_form.render(
                    LoginForm(username=username, password=password, next=next)
                )
            ]
        ]

    login_form = c.data.DataForm(
        name="app-login",
        routes=webapp,
        type=LoginForm,
        handle_submit=submit_login_form,
    )

    @webapp.page(login_path, title="Sign in")
    async def login_page(next: Annotated[str, Query()] = "") -> PageResponse:
        return PageResponse(
            node=await render_login_form(next=next),
            page_template=AppShell(mode="app", main_navigation=False, user_menu=False),
        )

    @webapp.page(logout_path, title="Sign out")
    async def logout_handler(request: Request) -> PageResponse:
        logout_user(request)
        return PageResponse.redirect(post_logout_redirect)
