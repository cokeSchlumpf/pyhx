# T-012 Modal dialogs: spec

## Requirements

### Component

- **R1** `pyhx.components` exports `dialog_content(children=None, *, title=None, actions=None, closable=True, close_url=None, id=DIALOG_CONTENT_ID, **kwargs)`, the swappable dialog: a `<dialog>` element with a header (the title as heading, which labels the dialog), the children, and a footer with the actions. Without children it renders closed and empty.
- **R2** `pyhx.components` exports `dialog(*, id=DIALOG_CONTENT_ID)`, the mount the page templates render once per page (backdrop and an empty `dialog_content`), and `DIALOG_CONTENT_ID = "dialog-content"`.
- **R3** A response that contains `dialog_content(...)` with children opens the dialog (out-of-band swap by id); a response with an empty `dialog_content()` closes it. A response can contain other out-of-band nodes as well (e.g. a `notification`, a changed list).
- **R4** `pyhx.components` exports `open_dialog_htmx_attributes(url, *, method="GET", as_dict=False, kwargs=None)`, so a button loads a dialog from a fragment route, like `open_drawer_htmx_attributes`.
- **R5** With `closable=True` the header has a close button (X) labelled "Close"; it posts to `close_dialog` (exported, returns an empty `dialog_content`), or to `close_url` when given, so the app can clean up its own state too. With `closable=False` (a required dialog) there is no close button.
- **R6** Children and actions are inside one `<form>`: an action is a `c.button` with `hx_post` (or another method) to a fragment route of the app, and the request carries the values of the controls in the dialog (e.g. a checkbox "Don't show this again") and the `name`/`value` of the clicked button.
- **R7** The fragment route of an action can answer by closing the dialog (R3), by returning `dialog_content(...)` again with changed content (e.g. an error at a field), or by `FragmentResponse.redirect(url)`; pyhx stores nothing about the answer.

### Modal behaviour

- **R8** While the dialog is open, the page behind it can't be used: its content is `inert` (no clicks, no focus, hidden from assistive technology), a backdrop covers it, and it doesn't scroll. The drawers and the notifications stay usable.
- **R9** The dialog closes only through its close button, through Escape, or through the response to an action. Escape acts like the close button, and only when the dialog has one and no drawer is open above it; a required dialog (`closable=False`) ignores Escape. A click on the backdrop never closes a dialog.
- **R10** There is one dialog at a time: a page has one mount; a dialog loaded while another is open replaces it.
- **R11** A drawer opened from a control in the dialog (e.g. `drawer_select`, the popup drawer) appears above the dialog and its backdrop, and works as it does on a page (including Escape, which closes the drawer, not the dialog).

### Page templates

- **R12** `CanvasShell` and `AppShell` take `dialog_content: SyncOrAsyncValue[y.Node | None] = None`, evaluated on every full page load like `header_content` of `CanvasShell`; when it returns a `dialog_content(...)`, the page is delivered with the dialog open. Both templates render the `dialog` mount.
- **R13** Existing apps don't change: without `dialog_content` the templates render an empty mount and nothing else differs.

### Focus and accessibility

- **R14** When the dialog opens, focus moves to the element with `autofocus` in it, or else to the dialog itself; when it closes, focus returns to the element that had it before (as with drawers), or else to the page's main content.
- **R15** Keyboard only: Tab reaches only the dialog's controls and actions (and a drawer above it); every action is a real `<button>`.
- **R16** The dialog has `aria-modal="true"` and is labelled by its title (`aria-labelledby`); the close button has an accessible name.

### Look

- **R17** The dialog looks as in the mockups of the intent, in the default design and in the canvas design, from the tokens of each design (no colours of its own).
- **R18** At 390 px width the dialog keeps 16 px from the edges, its content scrolls when it is taller than the screen while header and footer stay visible, and the actions stack at full width.

### Texts, samples, docs, tests

- **R19** The component's texts (the close button's label) are translated in de, it and fr.
- **R20** `samples/canvas_layout` has a page "Dialogs" with one "Show dialog" button each for: a required notice (a required confirmation with an error when it's missing, and a checkbox "Don't show this again"; the answer is shown in a notification, not stored), a confirmation before a destructive action, and a dialog with a `drawer_select`. No dialog opens without a click. `samples/components` (AppShell, default design) has a page "Dialog" with the same buttons for a notice and a confirmation.
- **R21** `docs/guides/dialogs.md` (in the nav under "Building Apps") explains the dialog: the guide below, final; `poe docs-build` passes.
- **R22** Tests: rendering of `dialog_content` (open, closed, closable, required, actions in the form), `close_dialog`, both templates with and without `dialog_content`, the CSS and JS rules for R8–R11 and R14 (read as text, as `test_drawer.py` does), and the sample pages with `TestClient`.

## Design

### Top layer: why the dialog is not `showModal()`

`dialog.showModal()` puts the dialog into the browser's top layer, above every `z-index`, and makes everything else inert, the drawers included. The drawers are `position: fixed` with `--hx-z-sidepanel` (200, popup 210/220), the notifications too. A modal dialog would cover them and block them, which breaks R11.

So the dialog is a `<dialog>` with the `open` attribute (non-modal in the browser's terms) at `--hx-z-dialog` (100, already in `theme.css` and so far unused for dialogs), below the drawers (200) and above the page header (90). The modality comes from pyhx: a backdrop, `inert` on the rest of the page, a scroll lock, `aria-modal="true"`. This is what `showModal()` does, minus the top layer, and it keeps the drawers as they are.

### Markup and flow

```
<div class="hx-dialog">                                  ← c.dialog(), rendered by the template
  <div class="hx-dialog__backdrop" aria-hidden="true"></div>
  <dialog id="dialog-content" open aria-modal="true"      ← c.dialog_content(...), swapped by id
          aria-labelledby="dialog-content__title"
          hx-ext="morph" hx-swap-oob="morph">
    <form hx-swap="none">
      <header><h2 id="dialog-content__title">Demo instance</h2> [close button]</header>
      <section>children</section>
      <footer>actions</footer>
    </form>
  </dialog>
</div>
```

- Opening and closing work like drawers: content is swapped out of band by id (`morph`), so any response can open, change or close the dialog. The server sets `open` when there are children; CSS shows the mount with `.hx-dialog:has(> dialog[open])`, and `html:has(.hx-dialog > dialog[open])` stops the page from scrolling.
- A page delivered with an open dialog (R12) needs no request and no script to show it.
- Actions sit in the form, so htmx sends the form's values with a non-GET request from a button inside it (R6). The form has no `hx-post` of its own: each action names its route, so a dialog can have actions to different routes ("Cancel" → `close_dialog`, "Delete" → the app's route).

### `pyhx.dialog.js`

A small script like `pyhx.drawer.js`, loaded by the skeleton:

- A `MutationObserver` on the mount notices `open` coming and going (also on page load).
- On open it sets `inert` on every child of `<body>` except the dialog mount, the two drawer mounts and the notifications, and remembers which ones it set; it moves focus (R14) and remembers where focus was.
- On close it removes only the `inert` it set and restores focus.
- Escape (R9, R11): when a drawer is open, `pyhx.drawer.js` closes the topmost drawer and the dialog does nothing. Otherwise, when the dialog is open and has a close button, `pyhx.dialog.js` clicks it (as `pyhx.drawer.js` clicks `[data-hx-drawer-close]`), so Escape posts to `close_dialog` or `close_url` like the X. It checks for an open drawer itself instead of relying on the order of the listeners, and skips events already `defaultPrevented`. It also cancels the dialog's native `cancel` event, so the browser never closes the dialog on its own.
- The backdrop has no click handler (R9).

Decision after the intent: the intent says a dialog never closes by Escape. In the spec review the developer decided that Escape closes a dialog that has a close button when no drawer is open above it (R9); required dialogs still ignore Escape.

### Page templates

`CanvasShell(dialog_content=...)` and `AppShell(dialog_content=...)` resolve the value with `resolve_value` on every full page load, as `CanvasShell` does with `header_content`, and render `dialog(...)` after the drawers with the result. A callable reads the current user through `RequestContext.get()` and returns `None` when nothing is to be shown. Fragments don't render the template, so the callable runs only on full page loads; after the user answered, the next page load asks it again.

### Look

- Width: at most 32 rem on the desktop, no size variants (the confirmation in the mockups is narrower only as a sketch). At phone width: `width: calc(100vw - 2rem)`, `max-height: calc(100dvh - 2rem)`, the `section` scrolls, the footer's buttons stack at full width.
- Canvas design: white surface, 12 px corners, borders between header, content and footer in `--hx-color-neutral-200`, backdrop `--hx-color-overlay-dark` (the drawers' backdrop), close button as in the drawer header, primary action in the text colour (as in forms).
- Default design: Roboto, 8 px corners, footer on `--hx-color-neutral-050`, primary action `appearance="primary"`, close button like the drawer's.
- New CSS file `static/css/pyhx/components/layout/dialog.css`, imported by `pyhx.css`; design differences through the tokens of `themes/canvas.css`, as for the drawer.

### Fragment route names

Component fragment paths are made from the handler's function name (`/_components/<name>/…`), and a second handler with the same name is skipped with only a warning. The close handler is therefore named `close_dialog` (`POST /_components/close_dialog/close`).

## Guide (first draft)

This is the first version of `docs/guides/dialogs.md`, to check the API and its use before it is built. The final guide is R21.

---

### Dialogs

A dialog asks the user something they must answer before going on: a notice to confirm, a confirmation before a destructive action, a short message. pyhx dialogs are modal: while one is open, the page behind it can't be used. They are opened and closed by the server, like drawers.

| Use | When |
| --- | --- |
| Drawer | Editing or viewing details beside the page; the user can close it any time. |
| Dialog | A question or notice the user must answer before going on. |

#### Showing a dialog

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

- `children` — the content; without children the dialog is closed.
- `title` — the heading; it also labels the dialog for screen readers.
- `actions` — the buttons in the footer, in order (the primary action last).
- `closable` — `True` (default) shows a close button (X); `False` makes the dialog required: only an action closes it.
- `close_url` — where the close button posts, instead of `c.close_dialog`, when the app must clean up on close.

A dialog closes through its close button, an action, or Escape, which works like the close button; a required dialog (`closable=False`) closes only through an action. A click beside a dialog never closes it. Only one dialog is open at a time: a dialog loaded while another is open replaces it.

#### Answering

Every action is a `c.button` with `hx_post` to a fragment route of the app. The values of all controls in the dialog are sent with it, and the `name` and `value` of the clicked button. The route answers in one of three ways:

```python
from typing import Annotated

from fastapi import Form
from pyhx.core import FragmentResponse


@router.fragment.post("/projects/{project_id}/delete")
async def delete_project(project_id: str) -> FragmentResponse:
    await projects.delete(project_id)
    return FragmentResponse.redirect("/projects")       # 1. go to another page


@router.fragment.post("/projects/{project_id}/archive")
async def archive_project(project_id: str) -> y.Node:
    await projects.archive(project_id)
    return y.fragment[
        c.dialog_content(),                             # 2. close the dialog …
        c.notification("Project archived.", appearance="success"),  # … and show more
    ]
```

The third way, returning `c.dialog_content(...)` again, changes the open dialog, e.g. to show an error at a field (see the notice below).

Pages and fragments also put a dialog into a response next to other nodes; any response with `c.dialog_content(...)` opens it.

#### A required notice on every page

A notice the user must confirm before using the app (e.g. terms of use) is shown by the page template. Give `CanvasShell` or `AppShell` a `dialog_content` callable: it runs on every full page load and returns the dialog, or `None` when nothing is to be shown.

```python
from typing import Annotated

import htpy as y
import pyhx.components as c
from commons.users import AnonymousUser
from fastapi import Form
from pyhx.core import RequestContext, WebApp
from pyhx.i18n import _
from pyhx.page_templates import CanvasShell


async def notice() -> y.Node | None:
    user = RequestContext.get().user
    if isinstance(user, AnonymousUser) or await notices.accepted(user.id):
        return None
    return notice_dialog()


def notice_dialog(error: str | None = None) -> y.Node:
    return c.dialog_content(
        y.p[_("This instance is for testing only. Use only synthetic test data.")],
        c.checkbox_fieldset(
            "",
            "accepted",
            [c.Option(label=_("I will upload only synthetic test data."), value="true")],
            error_text=error,
        ),
        c.checkbox_fieldset("", "dont_show_again", [c.Option(label=_("Don't show this again"), value="true")]),
        title=_("Demo instance"),
        closable=False,
        actions=[c.button(_("Accept"), appearance="primary", hx_post="/notice/accept")],
    )


hx = WebApp(title="My App", default_page_template=CanvasShell(dialog_content=notice))


@hx.fragment.post("/notice/accept")
async def accept_notice(
    accepted: Annotated[bool, Form()] = False,
    dont_show_again: Annotated[bool, Form()] = False,
) -> y.Node:
    if not accepted:
        return notice_dialog(error=_("Confirm this to continue."))
    await notices.accept(RequestContext.get().user.id, dont_show_again=dont_show_again)
    return c.dialog_content()
```

pyhx keeps no record of the answer: the app stores it and decides with it whether `notice()` shows the dialog again.

#### Controls with drawers

A control in a dialog that opens a drawer, e.g. `c.drawer_select`, opens it above the dialog. Escape closes that drawer first; the next Escape closes the dialog, if it has a close button.

#### Focus and keyboard

When a dialog opens, focus moves to the element with `autofocus` in it, or to the dialog. Give the safe choice `autofocus` in a confirmation (e.g. "Cancel"). When the dialog closes, focus returns to where it was. While a dialog is open, Tab moves only through the dialog (and a drawer above it).

#### Custom page templates

The page templates of pyhx render the dialog's mount. A template of your own renders `c.dialog()` once, after the drawers, at the end of `<body>`.

#### Samples

- `samples/canvas_layout`, page "Dialogs": buttons that show a required notice, a confirmation and a dialog with a drawer select (`poetry run fastapi dev samples/canvas_layout/main.py`).
- `samples/components`, page "Dialog": notice and confirmation in the default design.
- The `dialog_content` parameter of the page templates is shown above; the samples open their dialogs by button only, so they don't block the other sample pages.

---

## Alternatives considered

- **`showModal()` and the top layer:** the browser would do inert, focus and Escape. But it puts the dialog above the drawers and makes them inert (R11); moving the drawers and notifications into the top layer as well (as popovers) would change the drawers of every app for this change. Not chosen.
- **A centred drawer instead of `<dialog>`:** reuses the drawer code, but the intent asks for the native element and a drawer closes on a backdrop click and always on Escape, which a dialog must not.
- **`showModal()` only while no drawer is needed:** two modes for one component, and the dialog would have to know its content. Not chosen.
- **A dialog bound to a Pydantic model (`DataFormDialog`, like `DataFormDrawer`):** validation and live errors for free, but more API than a notice or a confirmation needs; children can contain a `DataForm` where an app wants one. Possible later.
- **A dialog per `PageResponse` instead of the template:** each page would have to add the notice itself, which the intent ruled out (shown "like drawers", from the page template).

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Additive minor release, apps opt in | R1–R5 new exports, R12 optional parameter, R13 |
| No new JavaScript dependency | `pyhx.dialog.js` (plain JS), htmx `morph` as drawers |
| Default and canvas design, 390 px | R17, R18 |
| Every text through `pyhx.i18n`, de/it/fr | R19 |
| Public repository: no client names, URLs, product screenshots | Samples and guide with neutral content (R20, R21) |
| Every dialog modal; closes only by X or an action | R8, R9 (Escape like the X, decided in the spec review) |
| One dialog at a time; drawers above it | R10, R11 |
| pyhx stores no answers | R7, guide |
| `hx_confirm` stays | Out of scope |

## Open questions

None.

## Areas of concern

1. **Modality without the top layer** (R8, R15): inert must cover everything but the dialog, the drawers and the notifications; something an app appends to `<body>` later is not inert. Handled by setting `inert` on the children of `<body>` when the dialog opens; checked by hand in both samples (keyboard only, screen reader smoke test with VoiceOver). Owner: Michael.
2. **No browser tests** (R8–R11, R14): pyhx has no browser test runner; the tests read CSS and JS as text. Behaviour is checked by hand with the samples during the implementation, with screenshots (desktop and phone width) in the change folder. Owner: Michael.
3. **Morph and `open`** (R3): idiomorph must add and remove the `open` attribute of the `<dialog>` and keep the focus inside when the content is replaced (an error after an answer). Checked in the sample's required notice. Owner: Michael.
4. **Stacking with existing z-indexes** (R11, R17): `--hx-z-dialog` (100) is above the page header (90) and below the drawers (200) and dropdowns (300); a dropdown of the page can't be opened while the page is inert. `table.css` uses `--hx-z-dialog` already; checked that it doesn't overlap. Owner: Michael.

## Out of scope

- The browser confirm of `hx_confirm` stays; replacing it with the dialog is a later change.
- Storing answers (pyhx stores nothing; the app does, e.g. CaseSight T-018).
- More than one dialog at a time, and dialogs above drawers.
- A dialog bound to a Pydantic model (`DataFormDialog`).
