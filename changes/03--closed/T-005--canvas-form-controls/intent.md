# T-005 Form controls for the canvas design

## Problem

The canvas design (`CanvasShell`, theme `themes/canvas.css`) restyles colours, type and cards, but not form controls. Inputs, selects, textareas, checkboxes and radios keep Pico's defaults: measured in `CanvasShell`, a text field is 50 px high with 16 px text next to 32 px buttons with 14 px text, the field has Pico's grey fill (`#FBFCFC`) and border (`#CFD5E2`), focus, checked boxes and primary buttons are blue (`#1E49E2`), and radii are 4 px where cards and the reference design (the GILAI demo) use 8 px. Labels are 16 px regular, help text 13.3 px pulled up by a negative margin. Forms in apps on the canvas design (case-sight) therefore look like a different product than the pages around them.

Accessibility is a requirement: the borders of controls must reach a contrast of at least 3:1 (WCAG 2.2, 1.4.11) and text at least 4.5:1 (1.4.3). The reference design uses lighter borders (about 1.3:1), so it can't be copied as is; the canvas palette's `neutral-300` (1.48:1) and `neutral-400` (2.58:1) don't reach 3:1, and the danger colour `#F54A00` (3.58:1) is enough for a border but not for error text.

The target look is drafted on the design canvas "Casesight Form Controls" (comparison, states and tokens, compact form in an aside).

## Proposed outcome

- In the canvas design, text fields, selects, textareas, checkboxes, radios and switches follow the canvas tokens: white field, 14 px text, 8 px radius, one height shared by fields and buttons, label above the field, help text below with even spacing.
- Neutral accent instead of blue in the canvas design: focus, checked controls and primary buttons use the canvas text colour.
- Every control border reaches at least 3:1 against white and the canvas background, error text at least 4.5:1; focus is clearly visible.
- States are defined and consistent: default, hover, focus, error, disabled, read-only.
- pyhx components built on these controls (form field, data form, dropdown, select fieldset, drawer radio and select, segment control) follow without changes in apps.
- The sample of the canvas design gets a page with forms in all states, including a compact form in an aside.
- The pull request shows screenshots before and after.
- The default theme (`AppShell`) doesn't change.

## Affected users and systems

- **PyHX (library):** `static/css/themes/canvas.css`; possibly the canvas-only parts of form and button styles under `static/css/pyhx/components/`.
- **Samples:** `samples/canvas_layout` (new forms page), its tests in `tests/samples`.
- **Documentation:** `docs/guides/layouts.md` (canvas design).
- **Apps on the canvas design** (case-sight): forms change their look with the next pyhx release; no code change needed.

## Constraints

- No change of the public Python API; released as `feat:`, no breaking change.
- `AppShell` and the default theme render exactly as before.
- WCAG 2.2 AA: 1.4.11 (3:1 for control boundaries and focus indicators), 1.4.3 (4.5:1 for text); disabled controls are exempt.
- Follows the CSS authoring conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`); no new dependency, no JavaScript.
- `poe check` and `poe docs-build` pass.

## Open questions

None.
