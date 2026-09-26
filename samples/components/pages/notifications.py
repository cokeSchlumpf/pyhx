"""Notification (toast) demo page + the fragments that emit them."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from fastapi import HTTPException
from pyhx.core import WebAppRouter
from pyhx.core.primitives import htmx
from pyhx.components.variants import Appearance
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()


# ---------------------------------------------------------------------------
# Fragments that emit a single notification each.
#
# The interesting bit is that the response is just the OOB notification —
# there is no in-band content. HTMX still requires a target, so the trigger
# buttons use `hx_target="body"` + `hx_swap="none"` to discard the in-band
# response while letting the OOB child apply via `beforeend:#hx-notifications`.
# ---------------------------------------------------------------------------

# docs:start fragment_handlers
@router.fragment.post("/notifications/info")
async def emit_info() -> y.Node:
    return c.notification(
        "Heads up — this is an informational message.",
        appearance="info",
        title="FYI",
    )


@router.fragment.post("/notifications/success")
async def emit_success() -> y.Node:
    return c.notification(
        "Your changes have been saved.",
        appearance="success",
        title="Saved",
    )


@router.fragment.post("/notifications/warning")
async def emit_warning() -> y.Node:
    return c.notification(
        "You're approaching your monthly quota.",
        appearance="warning",
        title="Almost there",
    )


@router.fragment.post("/notifications/danger")
async def emit_danger() -> y.Node:
    return c.notification(
        "Something went wrong while contacting the server.",
        appearance="danger",
        title="Request failed",
    )


@router.fragment.post("/notifications/timed")
async def emit_timed() -> y.Node:
    return c.notification(
        "This one removes itself after 3 seconds.",
        appearance="info",
        title="Auto-dismiss",
        timeout=3000,
    )


@router.fragment.post("/notifications/no-title")
async def emit_no_title() -> y.Node:
    return c.notification(
        "Compact toast — body only, no title.",
        appearance="neutral",
    )


@router.fragment.post("/notifications/non-dismissible")
async def emit_non_dismissible() -> y.Node:
    return c.notification(
        "No X button. Auto-removes after 4s instead.",
        appearance="primary",
        title="Persistent",
        timeout=4000,
        dismissible=False,
    )
# docs:end fragment_handlers


# ---------------------------------------------------------------------------
# Error-path demos. These trigger the client-side error handler in
# pyhx.app-shell.js, which clones the hidden <template> rendered by the
# notifications() mount and prepends it to the stack.
# ---------------------------------------------------------------------------


@router.fragment.post("/notifications/trigger-500")
async def trigger_500() -> y.Node:
    """Fires htmx:responseError — the JS handler shows a danger toast."""
    raise HTTPException(status_code=500, detail="Demo 500")


def _trigger(label: str, url: str, *, appearance: Appearance = "neutral") -> y.Node:
    """A button that POSTs to a fragment which emits a notification.

    `hx_swap="none"` discards the in-band response; the OOB notification
    still applies because OOB swaps run before the main swap is skipped.
    """
    return c.button(
        label,
        appearance=appearance,
        **htmx(
            hx_post=url,
            hx_target="body",
            hx_swap="none",
        ),
    )


@router.page("/notifications", title="Notifications")
async def notifications_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Notifications"],
            y.p[
                "Floating toast messages that stack in the bottom-right corner. ",
                "Each notification is emitted as an HTMX out-of-band fragment with ",
                y.code['hx-swap-oob="beforeend:#hx-notifications"'],
                " — multiple toasts coexist by appending to the container instead of replacing it.",
            ],
            y.h2["How it works"],
            y.p[
                "The ",
                y.code["notifications()"],
                " mount point is rendered once by the page template (",
                y.code["AppShell"],
                " already does this). Any fragment response can include a ",
                y.code["notification(...)"],
                " as an OOB sibling and HTMX appends it to the stack:",
            ],
            c.code([("code", src.text("oob_usage"), "python")]),
            y.p[
                "Dismissal is purely client-side — the X button's ",
                y.code["onclick"],
                " removes the closest ",
                y.code[".hx-notification"],
                " from the DOM. Auto-dismiss uses a one-line ",
                y.code['hx-on::load="setTimeout(() => this.remove(), N)"'],
                " — no extra HTMX extension required.",
            ],
            y.h2["Appearances"],
            y.p["One trigger per appearance — click to stack."],
            c.example(
                # docs:start appearances_demo
                y.div(
                    style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-block: 1rem;"
                )[
                    _trigger("Info", emit_info.url(), appearance="info"),
                    _trigger("Success", emit_success.url(), appearance="success"),
                    _trigger("Warning", emit_warning.url(), appearance="warning"),
                    _trigger("Danger", emit_danger.url(), appearance="danger"),
                ],
                # docs:end appearances_demo
                code=[
                    ("code", src.text("appearances_demo"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Auto-dismiss"],
            y.p[
                "Pass ",
                y.code["timeout=<ms>"],
                " to opt in. The notification self-removes after the delay; the X button still works in the meantime.",
            ],
            c.example(
                # docs:start timed_demo
                y.div(
                    style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-block: 1rem;"
                )[_trigger("Timed (3s)", emit_timed.url(), appearance="info"),],
                # docs:end timed_demo
                code=[("code", src.text("timed_demo"), "python")],
            ),
            y.h2["Variations"],
            y.p[
                "Title is optional; pass ",
                y.code["dismissible=False"],
                " for a notification that can only auto-clear (combine with ",
                y.code["timeout"],
                "). Both render via the same component.",
            ],
            c.example(
                # docs:start variations_demo
                y.div(
                    style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-block: 1rem;"
                )[
                    _trigger("No title", emit_no_title.url()),
                    _trigger(
                        "Non-dismissible", emit_non_dismissible.url(), appearance="primary"
                    ),
                ],
                # docs:end variations_demo
                code=[("code", src.text("variations_demo"), "python")],
            ),
            y.h2["HTMX errors"],
            y.p[
                "The ",
                y.code["notifications()"],
                " mount also renders a hidden ",
                y.code["<template>"],
                " carrying a notification skeleton. ",
                "A handler in ",
                y.code["pyhx.app-shell.js"],
                " listens for ",
                y.code["htmx:responseError"],
                ", ",
                y.code["htmx:sendError"],
                ", ",
                y.code["htmx:timeout"],
                ", and ",
                y.code["htmx:swapError"],
                " — on each, it clones the template, fills the title/content text nodes, and prepends it to the stack. ",
                "Works without a server roundtrip, so it survives network failures.",
            ],
            c.example(
                # docs:start errors_demo
                y.div(
                    style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-block: 1rem;"
                )[
                    _trigger("Trigger 500", trigger_500.url(), appearance="danger"),
                    # POST to a path that doesn't exist — FastAPI returns 404 →
                    # htmx:responseError. (To see htmx:sendError, throttle DevTools
                    # to "Offline" first.)
                    c.button(
                        "Trigger 404",
                        appearance="danger",
                        **htmx(
                            hx_post="/__does_not_exist__",
                            hx_target="body",
                            hx_swap="none",
                        ),
                    ),
                ],
                # docs:end errors_demo
                code=[("code", src.text("errors_demo"), "python")],
            ),
            y.h2["Stack behaviour"],
            y.p[
                "Click multiple buttons in quick succession — each one appends a new toast above the previous, with the slide-in animation playing per item. Closing one (X or auto-dismiss) leaves the others in place. This is the key difference vs. the ",
                y.a(href="/drawer")["drawer"],
                ", which replaces its content rather than stacking.",
            ],
            y.h2["Fragment handlers"],
            y.p[
                "Each trigger button POSTs to a fragment that returns an OOB notification. ",
                "Here is the full set of fragment handlers used on this page:",
            ],
            c.code([("code", src.text("fragment_handlers"), "python")]),
            y.h2["Example calls"],
            c.code([
                ("code", src.text("example_calls"), "python"),
                ("imports", src.text("imports"), "python"),
            ]),
        ]
    )


# ---------------------------------------------------------------------------
# Fenced source regions used only as code-block sources (not live demos).
# These comment blocks are real, renderable source — they cannot drift from
# what the page shows because they ARE the page source.
# ---------------------------------------------------------------------------

# docs:start oob_usage
# @router.fragment.post('/save')
# async def save() -> y.Node:
#     return [
#         main_response_node,                              # in-band
#         c.notification('Saved.',  appearance='success',  # OOB sibling
#                        timeout=4000),
#     ]
# docs:end oob_usage

# docs:start example_calls
# c.notification("Heads up.", appearance="info")
# c.notification("Saved.", appearance="success", title="Saved")
# c.notification("Almost there", appearance="warning",
#                title="Quota", timeout=5000)
# c.notification("Server error",  appearance="danger")
# c.notification("Persistent",    dismissible=False, timeout=4000)
# docs:end example_calls
