# Dialogs

A dialog asks the user something they must answer before going on: a notice to confirm, a confirmation before a destructive action, a short message. pyhx dialogs are modal: while one is open, the page behind it can't be used. They are opened and closed by the server, like drawers.

| Use | When |
| --- | --- |
| Drawer | Editing or viewing details beside the page; the user can close it any time. |
| Dialog | A question or notice the user must answer before going on. |

## Showing a dialog

A dialog is the component `c.dialog_content`. Return it from a fragment route and it opens; return an empty `c.dialog_content()` and it closes.

```python
import htpy as y

import pyhx.components as c
from pyhx.core import WebAppRouter

router = WebAppRouter()


@router.fragment.get("/projects/{project_id}/delete")
async def confirm_delete(project_id: str) -> y.Node:
    return c.dialog_content(
        y.p["“Aurora Migration” and its 3 files will be deleted. This can't be undone."],
        title="Delete project?",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url(), autofocus=True),
            c.button("Delete", appearance="danger", hx_post=f"/projects/{project_id}/delete"),
        ],
    )
```

A button loads it:

```python
c.button(
    "Delete",
    appearance="danger",
    **c.open_dialog_htmx_attributes(f"/projects/{project_id}/delete"),
)
```

Parameters of `c.dialog_content`:

- `*children` — the content, one node or several; without any the dialog is closed.
- `title` — the heading; it also labels the dialog for screen readers.
- `actions` — the buttons in the footer, in order (the primary action last). At phone width they stack across the full width, the last on top.
- `closable` — `True` (default) shows a close button (X); `False` makes the dialog required: only an action closes it.
- `close_url` — where the close button posts, instead of `c.close_dialog`, when the app must clean up on close.

A dialog closes through its close button, an action, or Escape, which works like the close button; a required dialog (`closable=False`) closes only through an action. A click beside a dialog never closes it. Only one dialog is open at a time: a dialog loaded while another is open replaces it.

## Answering

Every action is a `c.button` with `hx_post` to a fragment route of the app. The values of all controls in the dialog are sent with it, and the `name` and `value` of the clicked button. The route answers in one of three ways:

```python
from pyhx.core import FragmentResponse


@router.fragment.post("/projects/{project_id}/delete")
async def delete_project(project_id: str) -> FragmentResponse:
    await projects.delete(project_id)
    return FragmentResponse.redirect("/projects")  # 1. go to another page


@router.fragment.post("/projects/{project_id}/archive")
async def archive_project(project_id: str) -> y.Node:
    await projects.archive(project_id)
    return y.fragment[
        c.dialog_content(),  # 2. close the dialog …
        c.notification("Project archived.", appearance="success"),  # … and show more
    ]
```

The third way, returning `c.dialog_content(...)` again, changes the open dialog, e.g. to show an error at a field (see the notice below). Render the controls with the values the user sent, so a refused answer keeps their input.

Any response that contains `c.dialog_content(...)` opens the dialog, also next to other nodes of a page or fragment.

## A required notice on every page

A notice the user must confirm before using the app (e.g. terms of use) is shown by the page template. Give `CanvasShell` or `AppShell` a `dialog_content` callable: it runs on every full page load and returns the dialog, or `None` when nothing is to be shown.

```python
from typing import Annotated

import htpy as y
from commons.users import AnonymousUser
from fastapi import Form

import pyhx.components as c
from pyhx.core import RequestContext, WebApp
from pyhx.i18n import _
from pyhx.page_templates import CanvasShell


async def notice() -> y.Node | None:
    user = RequestContext.get().user
    if isinstance(user, AnonymousUser) or await notices.accepted(user.id):
        return None
    return notice_dialog()


def notice_dialog(error: str | None = None, dont_show_again: bool = False) -> y.Node:
    return c.dialog_content(
        y.p[_("This instance is for testing only. Use only synthetic test data.")],
        c.checkbox_fieldset(
            "",
            "accepted",
            [c.Option(label=_("I will upload only synthetic test data."), value="true")],
            error_text=error,
        ),
        c.checkbox_fieldset(
            "",
            "dont_show_again",
            [c.Option(label=_("Don't show this again"), value="true")],
            value=["true"] if dont_show_again else [],
        ),
        title=_("Demo instance"),
        closable=False,
        actions=c.button(_("Accept"), appearance="primary", hx_post="/notice/accept"),
    )


hx = WebApp(title="My App", default_page_template=CanvasShell(dialog_content=notice))


@hx.fragment.post("/notice/accept")
async def accept_notice(
    accepted: Annotated[bool, Form()] = False,
    dont_show_again: Annotated[bool, Form()] = False,
) -> y.Node:
    if not accepted:
        return notice_dialog(error=_("Confirm this to continue."), dont_show_again=dont_show_again)
    await notices.accept(RequestContext.get().user.id, dont_show_again=dont_show_again)
    return c.dialog_content()
```

pyhx keeps no record of the answer: the app stores it and decides with it whether `notice()` shows the dialog again. The callable runs on full page loads only; fragments don't render the page template.

## Controls with drawers

A control in a dialog that opens a drawer, e.g. `c.drawer_select`, opens it above the dialog. Escape closes that drawer first; the next Escape closes the dialog, if it has a close button.

## Focus and keyboard

When a dialog opens, focus moves to the element with `autofocus` in it, or to the dialog. Give the safe choice `autofocus` in a confirmation (e.g. "Cancel"). When the dialog closes, focus returns to where it was. While a dialog is open, Tab moves only through the dialog, a drawer opened above it and the notifications; the rest of the page is `inert`.

Enter in a text field triggers the first action, as in any form; the form itself is never submitted without htmx.

## How it works

The dialog is a `<dialog>` element, shown with its `open` attribute and swapped out of band by id (`hx-swap-oob="morph"`), like the drawers. It isn't shown with `showModal()`: the browser's top layer would put it above the drawers and make them inert. Instead it sits at `--hx-z-dialog`, below the drawers and above the page header, and `pyhx.dialog.js` (loaded by every page template) makes the rest of the page `inert` while it is open. Content that an app appends to `<body>` while a dialog is open is not made inert.

## Custom page templates

The page templates of pyhx render the dialog's mount. A template of your own renders `c.dialog()` once, after the drawers, at the end of `<body>`; `c.dialog(content)` delivers the page with that dialog open.

## Samples

- `samples/canvas_layout`, page `/dialogs`: buttons that show a required notice, a confirmation and a dialog with a drawer select (`poetry run fastapi dev samples/canvas_layout/main.py`).
- `samples/components`, page `/dialog`: notice and confirmation in the default design, with their code.

The samples open their dialogs by button only, so they don't block the other sample pages; `dialog_content` of the page templates is shown above.
