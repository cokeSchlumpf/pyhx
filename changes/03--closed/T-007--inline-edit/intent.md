# T-007 Inline editing of single values

## Problem

Detail pages show values that users correct one at a time while they look at something else next to them: in case-sight, values extracted from a document (start of incapacity, diagnosis, workload) are checked against the document and corrected in the aside. Today pyhx offers forms (`DataForm`) and the edit drawer; both edit a whole record and the drawer covers the page, so the document is no longer visible while correcting. Apps build their own forms for this: beleglotse has a hand-made correction form next to the document preview (`_invoice_detail.py`), which saves the whole invoice at once and isn't reusable.

`HeadlessForm` already provides the controller half (parsing, validation, touched fields, htmx wiring) without layout, so the missing part is a component for the "display a value, edit it in place, save it" pattern.

The target look is drafted on the design canvas "DataPage im CanvasShell" (https://claude.ai/artifact/5FmCxN9D8dG5cQVoLxqeE6, "Welches Muster wann", inline in the aside) and on "Casesight Form Controls" (compact form in an aside: Esc cancels, Enter saves).

## Proposed outcome

- A pyhx component shows a value (label, value, optional source and hint) with an edit action; activating it swaps that one value into a compact form in place.
- Enter (or the save button) validates and saves through a callback of the app; on success the value shows again with the new content, on errors the form stays with the messages at the field.
- Esc (or the cancel button) returns to the value without saving.
- Only one value is in edit mode at a time within a group; opening another one cancels the open one.
- It works with keyboard and screen reader: the edit action is a real button, focus moves into the field on opening and back to the edit action on closing.
- It fits in cards and their lists (`c.card.item`) and in the aside of a `split_layout`, in both designs, with the compact size of T-006 in the canvas design.
- `samples/canvas_layout` makes the "Extrahierte Angaben" card of the dossier page editable.
- Not part of this change: editing several values at once, editing table cells, autosave while typing, conflict detection between users.

## Affected users and systems

- **PyHX (library):** a new component built on `HeadlessForm`; possibly small additions to `HeadlessForm` where it lacks a hook; styles in both designs.
- **Samples:** `samples/canvas_layout` (dossier page), tests in `tests/samples` and `tests/pyhx/components`.
- **Documentation:** a guide section on editing patterns (drawer, detail page, inline).
- **Apps:** case-sight (correction of extracted values) first; beleglotse could replace parts of its correction form later.

## Constraints

- htmx and server-rendered fragments as elsewhere in pyhx; at most a small script for keyboard handling, no client-side framework.
- `HeadlessForm`'s existing API stays compatible.
- Uses the compact size of T-006; until T-006 is merged the component uses the default size.
- Accessibility: WCAG 2.2 AA; no global key handlers, keys handled on the form.

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal.

### Q1 What does the save callback get and return?

**Proposal:** The validated value of a small Pydantic model (one field, or a few that belong together) and returns the value to display, or raises a validation error that is shown at the field; the same shape as `HeadlessForm`'s submit handler.

**Answer:** Ok.

### Q2 Where is "one at a time" enforced?

**Proposal:** In the browser: opening a value cancels the open one of the same group (no request needed, unsaved input is dropped). The server stays stateless.

**Answer:** Ok.

### Q3 Branch base

**Proposal:** Branch from `main`; the component's markup and behaviour don't depend on T-006, only its compact look does, which follows when both are merged.

**Answer:** Ok.
