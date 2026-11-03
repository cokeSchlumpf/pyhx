"""Modal dialogs in the canvas design.

Included by :mod:`samples.canvas_layout.main`. ``/dialogs`` has one
"Show dialog" button each for

- a required notice: no close button, a confirmation that must be ticked (an
  error replaces the content when it isn't) and "Don't show this again"; the
  answer is shown in a notification, nothing is stored,
- a confirmation before a destructive action, with "Cancel" focused, and
- a dialog with a ``drawer_select``, whose drawer opens above the dialog.

No dialog opens without a click, so the other sample pages stay usable. How
a page template shows a notice on every page load is in the guide
``docs/guides/dialogs.md`` (``CanvasShell(dialog_content=...)``).
"""

from typing import Annotated

import htpy as y
from fastapi import Form

import pyhx.components as c
from pyhx.core import WebAppRouter
from pyhx.core.primitives import styles
from samples.components._snippets import snippets

router = WebAppRouter()
src = snippets(__file__)

OWNERS = tuple(
    c.Option(label=name, value=value)
    for value, name in (
        ("anna", "Anna Schmidt"),
        ("marco", "Marco Rossi"),
        ("sophie", "Sophie Martin"),
        ("lena", "Lena Fischer"),
        ("oliver", "Oliver Novak"),
        ("priya", "Priya Nair"),
    )
)


# docs:start notice
def _notice(error: str | None = None, dont_show_again: bool = False) -> y.Node:
    return c.dialog_content(
        y.p[
            "This instance is for testing only. Documents you upload are "
            "processed by cloud services hosted in the EU."
        ],
        c.checkbox_fieldset(
            "",
            "accepted",
            [c.Option(label="I will upload only synthetic test data.", value="true")],
            error_text=error,
        ),
        c.checkbox_fieldset(
            "",
            "dont_show_again",
            [c.Option(label="Don't show this again", value="true")],
            value=["true"] if dont_show_again else [],  # keeps the choice after an error
        ),
        title="Demo instance",
        closable=False,
        actions=c.button("Accept", appearance="primary", hx_post=accept_notice.url()),
    )


@router.fragment.get("/dialogs/notice")
async def show_notice() -> y.Node:
    return _notice()


@router.fragment.post("/dialogs/notice/accept")
async def accept_notice(
    accepted: Annotated[bool, Form()] = False,
    dont_show_again: Annotated[bool, Form()] = False,
) -> y.Node:
    if not accepted:
        return _notice(error="Confirm this to continue.", dont_show_again=dont_show_again)
    # A real app stores the answer here and asks it in `dialog_content`.
    again = "won't be shown again" if dont_show_again else "will be shown again"
    return y.fragment[
        c.dialog_content(),
        c.notification(f"Accepted. The notice {again}.", appearance="success"),
    ]
# docs:end notice


# docs:start confirm
@router.fragment.get("/dialogs/confirm")
async def show_confirm() -> y.Node:
    return c.dialog_content(
        y.p["“Aurora Migration” and its 3 files will be deleted. This can't be undone."],
        title="Delete project?",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url(), autofocus=True),
            c.button("Delete", appearance="danger", hx_post=delete_project.url()),
        ],
    )


@router.fragment.post("/dialogs/confirm/delete")
async def delete_project() -> y.Node:
    return y.fragment[
        c.dialog_content(),
        c.notification("Project deleted (in this sample nothing was deleted).", appearance="success"),
    ]
# docs:end confirm


# docs:start hand_over
@router.fragment.get("/dialogs/hand-over")
async def show_hand_over() -> y.Node:
    return c.dialog_content(
        y.p["Choose who takes over “Aurora Migration”."],
        c.drawer_select("owner", OWNERS, labels=c.DrawerSelectLabels(value_column="New owner")),
        title="Hand over project",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url()),
            c.button("Hand over", appearance="primary", hx_post=hand_over.url()),
        ],
    )


@router.fragment.post("/dialogs/hand-over")
async def hand_over(owner: Annotated[list[str], Form()] = []) -> y.Node:  # noqa: B006
    names = ", ".join(o.label for o in OWNERS if o.value in owner) or "nobody"
    return y.fragment[
        c.dialog_content(),
        c.notification(f"Handed over to {names}.", appearance="success"),
    ]
# docs:end hand_over


def _show(url: str) -> y.Node:
    return c.button("Show dialog", **c.open_dialog_htmx_attributes(url))


@router.page("/dialogs", title="Dialogs")
async def dialogs_page() -> y.Node:
    return y.div(**styles("flex", "flex-col", "gap-md"))[
        c.breadcrumbs(y.a(href="/")["Canvas Layout"], "Dialogs"),
        c.card[
            c.card.header[c.card.title[y.h1["Dialogs"]]],
            c.card.section[
                y.p[
                    "A dialog asks something the user must answer before going on. "
                    "It is opened and closed by the server, like a drawer: a fragment "
                    "route returns ",
                    y.code["c.dialog_content(...)"],
                    " to open it and an empty ",
                    y.code["c.dialog_content()"],
                    " to close it.",
                ],
            ],
        ],
        c.card[
            c.card.header[c.card.title[y.h2["Required notice"]]],
            c.card.section[
                y.p[
                    "No close button, Escape does nothing: only “Accept” closes it, "
                    "and only when the confirmation is ticked."
                ],
                c.example(_show(show_notice.url()), code=[("code", src.text("notice"), "python")]),
            ],
        ],
        c.card[
            c.card.header[c.card.title[y.h2["Confirmation"]]],
            c.card.section[
                y.p["Closes with the X, Escape or “Cancel” (focused when it opens)."],
                c.example(_show(show_confirm.url()), code=[("code", src.text("confirm"), "python")]),
            ],
        ],
        c.card[
            c.card.header[c.card.title[y.h2["A drawer above the dialog"]]],
            c.card.section[
                y.p[
                    "The drawer select opens its drawer above the dialog. Escape "
                    "closes the drawer first, then the dialog."
                ],
                c.example(_show(show_hand_over.url()), code=[("code", src.text("hand_over"), "python")]),
            ],
        ],
    ]
