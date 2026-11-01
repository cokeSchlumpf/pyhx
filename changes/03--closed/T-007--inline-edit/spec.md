# T-007 Inline editing of single values: spec

## Requirements

### Component

- **R1** `pyhx.components` exports `InlineEdit[T]` (`c.InlineEdit`), a component bound to a Pydantic model `T` (one field, or a few that belong together) and to an app's `load(key) -> T` and `save(key, value) -> T` callbacks; it registers its own fragments on the `routes` it is given (app or router), like `HeadlessForm`.
- **R2** `await item.render(key, value=None)` renders the value of the record `key` in display mode: label, value (formatted by an optional `display` callback), an optional hint (e.g. "unsicher gelesen") and an optional source (e.g. "Anmeldung S. 6"), both from optional callbacks of `(key, value)`, and an edit action; without `value` it calls `load(key)`.
- **R3** The edit action is a real `<button type="button">` with an `aria-label` naming the value (`"<edit_label>: <label>"`).
- **R4** Activating the edit action loads a form for that value into the item (one request) and hides the value and the edit action; the label, hint and source stay visible.
- **R5** The form has one control per model field (default: a text, number or date input from the field's type; a `fields` callback can render other controls), a primary save button, a cancel button and a short keyboard hint; the labels are configurable (`save_label`, `cancel_label`, `edit_label`, `shortcuts_hint`). A single-field form labels its control by the item's visible label.
- **R6** Saving validates the posted values against `T` and calls `save(key, value)`; on success the item returns to display mode with the value `save` returned.
- **R7** When validation fails, or `save` raises a `pydantic.ValidationError`, the form stays open with the message at the field (`form_field(error_text=…)`, `aria-invalid`, `aria-describedby`) and the entered input kept.
- **R8** Cancelling returns to display mode without saving and without a request; unsaved input is dropped.
- **R9** The server keeps no state between requests: the key travels in the request, the open/closed state lives in the browser.

### Keyboard, focus, groups

- **R10** Focus moves into the first control when the form opens, back to the item's edit button when it closes by cancel or save, and to the first invalid control when a save fails.
- **R11** Enter saves (also from a select), Esc cancels; both are handled by a listener on the form, not on the document.
- **R12** Only one item is in edit mode within a group: opening an item cancels the open one of the same group (focus stays in the new form). A group is the nearest ancestor with `data-hx-inline-edit-group`; items without one share the page as their group.
- **R13** The component works without the drawer and outside a `DataPage`.

### Look

- **R14** The item fits in a card list (`c.card.item`) and in the aside of a `split_layout`, in the default and in the canvas design; it is usable at 390px width.
- **R15** The component sets no control or button sizes of its own (it uses `form_field` and `c.button` at their default size), so the compact size of T-006 applies through its scope once merged.

### Samples, docs, tests

- **R16** `samples/canvas_layout`, dossier page: the four values of the card "Extrahierte Angaben" (Tätigkeit, Pensum, Beginn AU, Grad AU) are editable, kept in an in-memory store, with German labels; the aside has an editable value with a hint, as in the design.
- **R17** `samples/components` has an "Inline Edit" page (AppShell, default design) that shows the component in a card and documents its API, linked from the home page.
- **R18** `docs/guides` has a section on editing patterns: edit drawer, detail page, inline; `poe docs-build` passes.
- **R19** `tests/pyhx/components/test_inline_edit.py` covers display, edit fragment, valid and invalid submit, an error raised by `save`, the key round trip and the absence of a cancel request; `tests/samples` covers the dossier's editable values.

## Design

### API

```python
class Pensum(BaseModel):
    value: int = Field(ge=0, le=100)

pensum = c.InlineEdit[Pensum](
    routes=router,
    name="pensum",
    type=Pensum,
    label="Pensum",
    load=load_pensum,                    # async (key: str) -> Pensum
    save=save_pensum,                    # async (key: str, value: Pensum) -> Pensum
    display=lambda v: f"{v.value}%",     # optional: (T) -> Node
    source=lambda key, v: y.a(href="#")["Anmeldung S. 9"],  # optional: (str, T) -> Node
    hint=None,                           # optional: (str, T) -> Node | None
    fields=None,                         # optional: (FormRenderContext[T]) -> Node
    save_label="Korrektur speichern",
    cancel_label="Abbrechen",
    edit_label="Bearbeiten",
    shortcuts_hint="Esc abbrechen · ↵ speichern",
)

c.card.list(data_hx_inline_edit_group="angaben")[
    c.card.item[await pensum.render(dossier_id)],
]
```

The callbacks get the key, not the request: the app decides what a key is (a record id, or a record id and a field). Source and hint are callbacks of `(key, value)` rather than render arguments, because the server re-renders the item after a save without the page's context; this way the source can also change after a correction.

### Built on HeadlessForm

`InlineEdit` owns a `HeadlessForm[T]` named `inline-edit-<name>`: it gets parsing, validation and the error dict from it, and passes it a layout callback (the inline form) and a submit handler (call `save`, render the display out of band). `HeadlessForm` already catches a `ValidationError` raised by the submit handler and re-renders the form with every field touched, so R7 needs no change to `HeadlessForm` (its API stays as it is). The live validation fragment of `HeadlessForm` is registered but not wired: a single value is validated when it is saved.

`InlineEdit` adds one fragment, `GET /_components/inline-edit/<name>/edit?key=…`, which calls `load(key)` and returns the form. The form posts to the `HeadlessForm` submit fragment with `?key=…`; the layout callback and the submit handler read the key from the current request's query (`RequestContext.get_request()`), so the server needs no state (R9).

### Markup and flow

```
<div class="hx-inline-edit" id="hx-inline-edit--<name>--<key>">
  <span class="hx-inline-edit__label" id="…__label">Beginn AU</span>
  <span class="hx-inline-edit__hint">unsicher gelesen</span>
  <span class="hx-inline-edit__value">20.01.2026</span>
  <span class="hx-inline-edit__source">Anmeldung S. 6</span>
  <button class="hx-button … hx-inline-edit__edit" aria-label="Bearbeiten: Beginn AU"
          hx-get="…/edit?key=…" hx-target="#…" hx-swap="beforeend">✎</button>
  <!-- edit mode: -->
  <form class="hx-inline-edit__form" id="…__form" hx-post="…/submit?key=…" hx-swap="none">
    form_field(s) · [Korrektur speichern] [Abbrechen] · Esc abbrechen · ↵ speichern
  </form>
</div>
```

- Open: the edit button appends the form to the item; CSS hides the value and the button while the item `:has()` a form (state via `:has`, CSS conventions §4).
- Save, valid: the response is the item in display mode with `hx-swap-oob="outerHTML"`, replacing the item and with it the form.
- Save, invalid: the response is the form with `hx-swap-oob="morph"` (as `HeadlessForm` does), keeping the input.
- Cancel: the script removes the form; no request.

The item id encodes the key (characters other than letters, digits, `-` and `_` are escaped), so the out-of-band responses find the item. A single-field form labels its control with `aria-labelledby` pointing at the item's label, so the label isn't repeated above the field; forms with several fields use `form_field` labels from the field `title` (or the field name).

### Script

`static/js/pyhx.inline-edit.js`, loaded by the `Skeleton` like the other pyhx scripts. On `htmx:load` of a form it cancels the other open form of the same group, binds `keydown` (Esc, Enter on a select) and the cancel button on the form, and focuses the first control; when a saved item is swapped in it focuses its edit button; after a failed save it focuses the first invalid control.

### CSS

`static/css/pyhx/components/data/inline_edit.css` in the `pyhx` layer: the item is a two-column grid (content, edit button); the form spans the item. Text sizes from the role tokens, colours from theme tokens (hint in the warning text colour), no own control sizes (R15). The canvas design needs no overrides beyond what cards already do.

## Alternatives considered

- **Extend `DataForm` with an inline mode:** `DataForm` lays out a whole record from annotations and its submit replaces the form; an inline value needs a display mode, a key and a different layout, so it would add a second component inside the first.
- **Cancel by request (re-render the display from `load`):** simpler script, but every cancel and every "open another" costs a request, and the developer's answer to Q2 of the intent asks for no request.
- **Keep the display markup in a `<template>` and swap the whole item on open:** duplicates the display in the DOM; hiding parts with `:has()` needs nothing extra.
- **Pass source and hint to `render`:** they'd be lost when the server re-renders the item after a save.
- **One generic store-backed component (field paths on a record):** shorter for apps with one record type, but ties the component to a storage shape; `load`/`save` per value leave that to the app.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| htmx and server-rendered fragments; at most a small script, no framework | Design "Built on HeadlessForm", "Script" (R4, R6, R11, R12) |
| `HeadlessForm`'s API stays compatible | Not changed; `InlineEdit` uses it as it is |
| Compact size of T-006; default size until merged | R15 |
| WCAG 2.2 AA; no global key handlers, keys on the form | R3, R5, R7, R10, R11 |
| Q1: callback gets the validated model, returns the value to display or raises a validation error | R6, R7 |
| Q2: one at a time in the browser, server stateless | R8, R9, R12 |
| Q3: branch from `main` | Branch `feature/inline-edit` from `main` |

## Open questions

None left: the developer answered the intent's questions and asked for the change to be implemented without stopping. Decisions taken while specifying, without asking:

- Name and shape: a class `InlineEdit[T]` with `load`/`save` callbacks per value and a key per record (not a function component), so it can register its fragments like `HeadlessForm`.
- A group is the nearest ancestor with `data-hx-inline-edit-group`, the page by default (the design's "1 in Bearbeitung" counts per page).
- The label stays visible in edit mode and labels a single control; no extra "Wert" label.
- Labels of the buttons and the keyboard hint are parameters with English defaults (the samples pass German ones); translations are left to the i18n work.
- No live validation while typing; the value is validated when it is saved.
- The "1 in Bearbeitung" counter of the design is not built: with one item per group it would always say 1.

## Areas of concern

1. **Ids of `form_field`** (R7): `form_field` derives the help text id from the field name, so two open forms with the same field name (in two groups) share an id. One open form per page is the default; documented, not solved here. Owner: Michael Wellner.
2. **Focus after out-of-band swaps** (R10): depends on htmx firing `htmx:load` for the out-of-band item and on idiomorph keeping the form; checked in the browser (Chromium) in the screenshot script. Owner: Michael Wellner.
3. **Compact look** (R15): the label-left layout and the 32px/28px sizes of the design come with T-006; until then the form uses the default size and the label above the field. Owner: Michael Wellner.
4. **Browsers:** checked in Chromium only. Owner: Michael Wellner.

## Out of scope

- Editing several values at once, table cells, autosave, conflict detection (intent).
- The compact size and the label-left layout (T-006).
- A count of open items, and translations of the default labels (i18n work).

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **F1** `HeadlessForm` already catches a `ValidationError` raised by its submit handler, so errors raised by `save` show at the field without a change to `HeadlessForm`; its API is unchanged.
- **F2** The layout of a `HeadlessForm` chooses the form's id, so each inline form carries a per-item id and is still morphed out of band after a failed save.
- **F3** The inline form drops `HeadlessForm`'s `hx-include="[data-hx-include='always']"`: with nothing to include, htmx logged an error on every save.
- **F4** htmx 2.0.4 fires `htmx:load` for the out-of-band item and for the morphed form, so focus after save and after a failed save needs no other event; the script guards against binding a morphed form twice.
- **F5** The form gets the focus once htmx has settled the swap (about 20 ms after the response); keys typed in that moment go to the page.
- **D1** The card "Extrahierte Angaben" of the dossier sample starts expanded (`open=True`) instead of collapsed, so the editable values are visible; it stays collapsible.
- **D2** The label and the hint share a heading line (`hx-inline-edit__heading`), so the hint follows the label as in the design instead of sitting at the right edge.
- **D3** After merging `main` (T-005 multilingual apps, canvas form controls): the default texts are `pyhx.i18n` texts with de/it/fr catalog entries ("Save", "Cancel", "Esc cancels · ↵ saves", and "Edit {label}" as the edit button's accessible name). `edit_label` is now the whole accessible name (default "Edit <label>", translated) instead of a prefix joined with the label, so translations can order the words; the dossier sample passes only its own save label ("Korrektur speichern").
- **D4** The canvas form controls give `.hx-form-field` a bottom margin; the inline form's fields sit in a column with a gap instead, with the margin reset in the canvas scope too. (Sizes: see D5.)
- **D5** Amendment after merging T-006 (compact size, PR #29), replacing R15's "sets no sizes of its own": `InlineEdit` takes `size` and `label_position` like `DataForm` (default `None`: follow the place) and renders them on its `<form>`. In the canvas design the form is compact in the aside of a `split_layout` or in a drawer, or with `size="sm"`: 32px fields and 13px labels from `form_field`, 12px between fields and 28px buttons from `inline_edit.css`; in the main column it stays full size (36px). The fields are a one-column `hx-grid`, so the canvas design spaces them by the grid's gap. A single field gets `label_position="top"` and no label text of its own (the item's label names it), so a compact place reserves no empty label column next to the field; forms with several fields put their labels left where a field's cell is at least 360px wide, which the dossier aside (about 310px) is not, so its labels stay above the fields there, unlike the 64px label column of the design draft.
- **F6** `form_field` derives the ids of its label and help text from the field name only, so two open forms with the same field name in two groups share ids. Fixing it needs an id prefix on `form_field` (a primitive outside this component), so it is left open below.
- **F7** The screenshots are kept in `screenshots/` next to this spec, all in `de-CH`. Dossier page of `samples/canvas_layout`: [before](screenshots/canvas-shell--dossier--before.png) (before this change, the collapsed card opened by hand), [values displayed](screenshots/canvas-shell--dossier--desktop.png), [in edit mode](screenshots/canvas-shell--dossier--edit.png) (focus in the field), [validation error](screenshots/canvas-shell--dossier--error.png), [after saving](screenshots/canvas-shell--dossier--saved.png) (focus back on the edit button), [aside in edit mode](screenshots/canvas-shell--dossier--aside-edit.png), [aside after the correction](screenshots/canvas-shell--dossier--aside-saved.png), [phone](screenshots/canvas-shell--dossier--phone.png); "Inline Edit" page of `samples/components`: [desktop](screenshots/app-shell--inline-edit--desktop.png), [validation error](screenshots/app-shell--inline-edit--error.png).

Checked in Chromium with a Playwright script against both samples (Enter saves, Esc and the cancel button cancel without a request, opening a second item of a group closes the first, focus into the field and back to the edit button, focus to the invalid field, no horizontal overflow at 390px, no console errors).

Rollout: with the pull request of `feature/inline-edit`, released as a `feat` of pyhx.

Open after this change:

- Labels left of the fields in a narrow aside (the draft's 64px label column): T-006 moves a label left only from 360px per field; a narrower threshold would be a change of `form_field`. Owner: Michael Wellner.
- Duplicate `form_field` ids when two forms with the same field name are open in two groups (F6): an id prefix for `form_field`. Owner: Michael Wellner.
