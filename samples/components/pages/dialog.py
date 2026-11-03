"""Dialog demo page (default design) + the fragments that open and answer them."""

# docs:start imports
from typing import Annotated

import htpy as y
from fastapi import Form

import pyhx.components as c
from pyhx.core import WebAppRouter
# docs:end imports

from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()


# docs:start notice
def notice(error: str | None = None, dont_show_again: bool = False) -> y.Node:
    return c.dialog_content(
        y.p["This instance is for testing only. Use only synthetic test data."],
        c.checkbox_fieldset(
            "",
            "accepted",
            [c.Option(label="I will use only synthetic test data.", value="true")],
            error_text=error,
        ),
        c.checkbox_fieldset(
            "",
            "dont_show_again",
            [c.Option(label="Don't show this again", value="true")],
            value=["true"] if dont_show_again else [],  # keeps the choice after an error
        ),
        title="Demo instance",
        closable=False,  # required: no close button, Escape does nothing
        actions=c.button("Accept", appearance="primary", hx_post=accept.url()),
    )


@router.fragment.get("/dialog/notice")
async def show_notice() -> y.Node:
    return notice()


@router.fragment.post("/dialog/notice/accept")
async def accept(
    accepted: Annotated[bool, Form()] = False,
    dont_show_again: Annotated[bool, Form()] = False,
) -> y.Node:
    if not accepted:
        return notice(error="Confirm this to continue.", dont_show_again=dont_show_again)  # replaces the content
    return y.fragment[
        c.dialog_content(),  # closes the dialog
        c.notification(
            f"Accepted (don't show again: {'yes' if dont_show_again else 'no'}).",
            appearance="success",
        ),
    ]
# docs:end notice


# docs:start confirm
@router.fragment.get("/dialog/confirm")
async def show_confirm() -> y.Node:
    return c.dialog_content(
        y.p["“Aurora Migration” and its 3 files will be deleted. This can't be undone."],
        title="Delete project?",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url(), autofocus=True),
            c.button("Delete", appearance="danger", hx_post=delete.url()),
        ],
    )


@router.fragment.post("/dialog/confirm/delete")
async def delete() -> y.Node:
    return y.fragment[
        c.dialog_content(),
        c.notification("Project deleted (in this sample nothing was deleted).", appearance="success"),
    ]
# docs:end confirm


@router.page("/dialog", title="Dialog")
async def dialog_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Dialog"],
            y.p[
                "A modal dialog asks something the user must answer before going on. ",
                "A fragment route returns ",
                y.code["c.dialog_content(...)"],
                " to open it (any response can, out of band) and an empty ",
                y.code["c.dialog_content()"],
                " to close it. Only one dialog is open at a time; while it is open, ",
                "the page behind it can't be used. Guide: ",
                y.code["docs/guides/dialogs.md"],
                ".",
            ],
            y.h2["Required notice"],
            y.p[
                y.code["closable=False"],
                ": no close button, Escape and a click beside it do nothing. ",
                "“Accept” without the confirmation returns the dialog again with an error.",
            ],
            c.example(
                # docs:start show_notice
                c.button("Show dialog", **c.open_dialog_htmx_attributes(show_notice.url())),
                # docs:end show_notice
                code=[
                    ("button", src.text("show_notice"), "python"),
                    ("fragments", src.text("notice"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Confirmation"],
            y.p[
                "Closes with the X, Escape or “Cancel”, which has ",
                y.code["autofocus"],
                " so the safe choice is focused when the dialog opens.",
            ],
            c.example(
                c.button("Show dialog", **c.open_dialog_htmx_attributes(show_confirm.url())),
                code=[("fragments", src.text("confirm"), "python")],
            ),
        ]
    )
