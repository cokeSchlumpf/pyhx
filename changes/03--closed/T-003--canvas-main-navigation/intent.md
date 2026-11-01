# T-003 Main navigation for the canvas design

Written after the change was merged (PR #17): the change skipped the change workflow, see the Outcome in `spec.md`.

## Problem

The canvas design (`CanvasShell`, design `canvas`) has a top bar and a grey canvas, but no place for a main menu: it receives the app's navigation (`hx.navigation`) and doesn't render it. Pages built for it so far (the dossier views of `samples/canvas_layout`) don't need a menu, but apps on the canvas also need pages with a navigation, e.g. admin pages with many entries. Today such an app has to switch to `AppShell`, a different design.

## Proposed outcome

- `CanvasShell` can show a main navigation, optionally and per page.
- Pages built for the canvas without a menu render exactly as before.
- The navigation comes from `hx.navigation`, as in `AppShell`, so menus are declared the same way in both designs.
- One app can have different menus for different areas, e.g. its main areas and its admin pages.
- It works on a phone.
- The sample of the canvas design shows pages with and without a navigation side by side.

## Affected users and systems

- **PyHX (library):** `page_templates/canvas_shell.py`, its stylesheet `static/css/page-templates/canvas-shell.css`, the exports of `pyhx.page_templates`.
- **Samples:** `samples/canvas_layout`.
- **Documentation:** `docs/guides/layouts.md`.
- **Apps on the canvas design** (e.g. case-sight): can add a menu; nothing changes for them otherwise.

## Constraints

- An addition to the public API, released as `feat:`; no breaking change.
- No new dependency; JavaScript only where HTML and CSS can't do it.
- Follows the CSS authoring conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`).
- `poe check` and `poe docs-build` pass.

## Open questions

None.
