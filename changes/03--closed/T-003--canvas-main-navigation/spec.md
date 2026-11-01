# T-003 Main navigation for the canvas design: spec

Written after the change was merged (PR #17); it records what was built and decided, see the Outcome.

## Requirements

### Template

- **R1** `CanvasShell` takes `main_navigation: CanvasShellNavigation | None = None`, with `CanvasShellNavigation = Literal["tabs", "sidebar"]` exported from `pyhx.page_templates`.
- **R2** `CanvasShell` takes `navigation_slot: str = "main"`, the slot of `hx.navigation` it renders.
- **R3** Without `main_navigation`, or when the slot has no menu, the markup is the same as before the change (no `data-hx-navigation` attribute, body directly in `.hx-canvas-shell__content`).
- **R4** The active item is marked with `class="active"` and `aria-current="page"`, from the URL as in `AppShell` (`NavItem.is_active`).

### Tabs

- **R5** `main_navigation="tabs"` renders the menu as a row of tabs below the top bar, inside the sticky header and aligned with the content column; the active tab is underlined (square, no radius).
- **R6** A group of the menu (a dict entry with a label) opens as a dropdown; at most one is open; it closes on a click outside and on Escape, and works without JavaScript.
- **R7** `--hx-sticky-top` includes the tab row, so drawers, notifications and sticky elements sit below it.

### Sidebar

- **R8** `main_navigation="sidebar"` renders the menu as a column on the canvas, left of the content, sticky below the top bar, without a box of its own; the active item is a white pill; groups have a label.
- **R9** With `mode="full"` the sidebar sits at the left edge with its own padding and a border.

### Phone

- **R10** Below 768px the tab row and the sidebar scroll sideways in a row; the page is never wider than the viewport.

### Sample, docs, tests

- **R11** `samples/canvas_layout` shows pages with tabs (slot `main`) and admin pages with a sidebar (slot `admin`, one in `mode="full"`) next to its pages without navigation.
- **R12** `docs/guides/layouts.md` documents the parameters and the slots; `poe docs-build` passes.
- **R13** `tests/pyhx/page_templates/test_canvas_shell.py` covers R3, R5, R6 (markup and script loading), R8, R4 and R2.

## Design

### Template

`CanvasShellNavRenderer` subclasses `NavRenderer` like `AppShellNavRenderer`: items are `li > a` with an optional icon (in the sidebar and in tab dropdowns only; a tab row reads better as words), groups are a `<details name="hx-canvas-nav">` dropdown in the tabs and an `h3` with a list in the sidebar. `render_empty` returns `None`, which the shell uses to fall back to the markup without navigation (R3). The body gets `data-hx-navigation` with the placement; the tabs are rendered into the `<header>`, the sidebar into `.hx-canvas-shell__content` next to a new `.hx-canvas-shell__page` that holds the body.

### Slots

Navigation slots already exist in PyHX (`hx.navigation.set(nav, slot=...)`, `NavFactory`); `AppShell` renders only the slot `main`. `navigation_slot` (R2) lets one app render tabs from `main` on its pages and a sidebar from `admin` on its admin pages, chosen per page with `PageResponse(page_template=...)`.

### CSS

All rules live in `canvas-shell.css` (templates layer), scoped to the body. Pico styles `nav ul`, `nav li` and `nav a` (row layout, centred items, negative margins, padding, radius); the rules reset these where they matter. The tab row scrolls (`overflow-x: auto`), which would clip an absolutely positioned dropdown; the dropdown is `position: fixed` without offsets, which keeps it at its static place, and the header's `backdrop-filter` makes the header its containing block, so it escapes the row's clip. `--tabs--height` is `0px` without tabs, so `--hx-sticky-top` stays the top bar.

The body grid gets `grid-template-columns: minmax(0, 1fr)`: with an `auto` column, nowrap `header_content` widened the whole page past a phone's viewport (also without navigation).

### Closing the dropdown

`static/js/pyhx.canvas-shell.js` closes an open dropdown on a click outside it and on Escape (focus back to its summary). The shell loads it only with `main_navigation="tabs"`.

## Alternatives considered

- **Only one placement:** tabs don't scale to the many grouped items of admin pages; a sidebar takes width the dossier views need. Both were kept, chosen per page.
- **A navigation inside the top bar:** no room next to brand and `header_content`, especially on a phone.
- **Popover API for the dropdown:** light dismiss and Escape without JavaScript, but a popover sits in the top layer and needs CSS anchor positioning to stay below its tab, which isn't stable in every browser yet; otherwise it needs JavaScript to position it.
- **Reuse `pyhx.dropdown.js`:** it only closes single-select dropdowns on a pick.
- **A separate sample app:** built first as `samples/canvas_navigation`, then merged into `samples/canvas_layout`, so the canvas design has one sample.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| An addition, released as `feat:` | R1, R2 with defaults; R3 |
| No new dependency; JavaScript only where needed | R6: one small script, loaded only with tabs; the dropdown works without it |
| CSS authoring conventions | Design, "CSS": templates layer, sections, property order, state via data attributes |
| `poe check` and `poe docs-build` pass | R12, R13 |

## Open questions

None.

## Areas of concern

1. **Long `header_content` on a phone** (R10): the page no longer overflows, but the header's right side is cut off instead of wrapping or collapsing. Owner: Michael Wellner.
2. **Browsers:** checked in Chromium only, not in Safari or Firefox (the fixed dropdown inside a `backdrop-filter` header in particular). Owner: Michael Wellner.

## Out of scope

- A navigation in `AppShell` beyond its existing slot `main`.
- A user menu in the canvas top bar.

## Outcome

Implemented as specified, but **without the change workflow**: the developer asked for a design proposal on a separate branch, and the agent took the request's `/design` as the branch prefix and built it on `design/canvas-main-navigation` instead of `feature/<slug>`, without intent, spec or plan and without their acceptance. The developer reviewed it in the sample app and in the PR instead. This record (intent and spec) was written after the merge; there was no plan.

Decisions taken during the review:

- **D1** Both placements and the plain canvas stay (R5, R8, R3).
- **D2** The tab underline has no radius (R5).
- **D3** The dropdown closes on a click outside and on Escape with a small script, not with the Popover API (R6, see Alternatives).
- **D4** The sample lives in `samples/canvas_layout`, not in its own app (R11).

Findings:

- **F1** Pico's `nav` styles (row layout, centred items, negative margins, radius on links) leaked into both placements and had to be reset.
- **F2** On a phone the page was wider than the viewport, also without navigation: the body grid column was `auto` (fixed, see Design). A raw `<table>` in the sample widened it as well; the sample wraps it in a scrolling container.

Rollout: PR #17 (`feat: add an optional main navigation to CanvasShell`), squash-merged; the release (presumably 1.2.0) follows with the next Release PR. The screenshots in the PR description live on the branch `design/canvas-main-navigation-screenshots`, kept so they stay visible.

Open after this change: the areas of concern 1 and 2. Owner: Michael Wellner.
