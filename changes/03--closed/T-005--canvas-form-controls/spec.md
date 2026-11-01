# T-005 Form controls for the canvas design: spec

## Requirements

All requirements of the groups "Controls", "Fields" and "Buttons and segment control" apply to the canvas design (`data-hx-design="canvas"`) only.

### Controls

- **R1** Text inputs (all `<input>` types except checkbox, radio, range and file), selects and textareas render with white background, the canvas text colour, 14 px text (`--hx-text-control`), 8 px radius (`--hx-radius-lg`) and a height of 36 px for single-line controls; placeholders are `neutral-500`.
- **R2** At rest, the border of every control (text input, select, textarea, checkbox, radio, switch track) reaches at least 3:1 against white, `#FAFAFA` and the canvas background `#EEEEEE`; on hover it darkens to `neutral-500`.
- **R3** On focus, a control shows a border in the canvas text colour and a 3 px ring around it; the focused border reaches at least 3:1 against the resting border's surroundings.
- **R4** A control with `aria-invalid="true"` has a `danger-600` border (at least 3:1) and a ring in the danger colour on focus; a control with `aria-invalid="false"` keeps the neutral border.
- **R5** A read-only text control (`readonly`) has a dashed border and a `neutral-050` background; a disabled control has a `neutral-100` background, `neutral-500` text and is visibly different from an enabled one.
- **R6** Checkboxes and radios are 16 px; checked, they fill with the canvas text colour; a switch's track is the border colour of R2 when off and the canvas text colour when on.

### Fields

- **R7** The label of a form field is 14 px (`--hx-text-item`), medium weight, `neutral-700`; labels of checkbox and radio options are regular weight in the text colour.
- **R8** Help text below a control is 12 px (`--hx-text-meta`) in `neutral-500`; error help text and the required marker reach at least 4.5:1 against white (`danger-700`); success help text stays `success-600`.
- **R9** Spacing in a field: label to control 6 px, control to help text 6 px; consecutive fields 16 px apart.

### Buttons and segment control

- **R10** `button(...)` has an 8 px radius and the height of the controls (R1) in size `md`, 28 px in size `sm`.
- **R11** `button(..., appearance="primary")` uses the canvas text colour: as fill for `solid`, as text and border colour for `outline`, `ghost` and `link`.
- **R12** The checked option of `segment_control` fills with the canvas text colour; its keyboard focus outline is the canvas text colour.

### Components and default design

- **R13** `form_field`, `DataForm`, `dropdown`, `drawer_radio`, `drawer_select`, `select_fieldset` and `switch` render according to R1–R12 in the canvas design without changes to their Python API.
- **R14** Pages in the default design (`AppShell`) and the plain design render exactly as before.

### Sample, documentation, pull request

- **R15** `samples/canvas_layout` has a page "Forms", linked from its overview: a case form built with `DataForm` in a card, a grid of all controls in every state of R1–R12, and a compact correction form in the aside of a split layout. A test in `tests/samples` renders the page.
- **R16** The canvas section of `docs/guides/layouts.md` describes the form controls of the canvas design and their contrast rules.
- **R17** The pull request shows screenshots of the forms page before and after the change, and of a form in the default design (unchanged).

## Design

The change follows the pattern the canvas design already uses for cards, pills and the chronicle: values as tokens in `themes/canvas.css` (unlayered, `:root` only), and rules that need the design as `[data-hx-design="canvas"] …` in the component stylesheets of the `pyhx` layer.

**Tokens (`themes/canvas.css`).** Pico reads most of the form look from custom properties on `:root`; the canvas theme sets them:

```css
--pico-border-radius:                       var(--hx-radius-lg);        /* 8px */
--pico-form-element-spacing-vertical:       0.3125rem;                  /* 36px controls */
--pico-form-element-spacing-horizontal:     0.625rem;
--pico-form-element-background-color:       var(--hx-color-background);
--pico-form-element-border-color:           #878787;                    /* 3.59:1 on white, 3.10:1 on #EEEEEE */
--pico-form-element-color:                  var(--hx-color-text);
--pico-form-element-placeholder-color:      var(--hx-color-neutral-500);
--pico-form-element-active-border-color:    var(--hx-color-text);
--pico-form-element-focus-color:            rgb(23 23 23 / 0.10);
--pico-form-element-invalid-border-color:   var(--hx-color-danger-600);
--pico-form-element-invalid-active-border-color: var(--hx-color-danger-600);
--pico-form-element-invalid-focus-color:    rgb(245 74 0 / 0.15);
--pico-form-element-valid-border-color:     #878787;
--pico-form-element-valid-active-border-color: var(--hx-color-text);
--pico-form-element-valid-focus-color:      rgb(23 23 23 / 0.10);
--pico-primary-background / -border / -hover-background / -focus: the canvas text colour (checked checkbox, radio, switch; Pico's own buttons)
--pico-switch-background-color:             #878787;
--pico-switch-checked-background-color:     var(--hx-color-text);
--pico-muted-color:                         var(--hx-color-neutral-500);
--hx-color-danger-700:                      #CA3500;                    /* orange-700, 5.22:1 on white */
```

The theme does not change `--hx-color-primary` or `--hx-color-secondary`; links, tabs, metric tiles, bubbles and notifications keep their colours. `pyhx/theme.css` gets `--hx-color-danger-700` too (a darker step of its red), so both themes carry the same token names (CSS authoring conventions, §10).

**Rules for what Pico has no property for.**

- `pyhx/elements/form.css` (new, imported in `pyhx.css` like `elements/a.css`): text size of controls (R1), hover border (R2), focus ring width (R3: Pico sets `--pico-outline-width` on the element), read-only and disabled look (R5), checkbox and radio size (R6). Since the `pyhx` layer beats `pico`, these rules restate the error state where they set a border, so R4 keeps working.
- `pyhx/components/primitives/form_field.css`: label and help text typography, error colour, spacing (R7–R9), scoped to the canvas design.
- `pyhx/components/primitives/button.css`: radius and height (R10), primary colour (R11), scoped to the canvas design, like `pill.css`.
- `pyhx/components/primitives/segment-control.css`: checked fill and focus outline (R12).

Components that build on Pico's controls (`dropdown` with `details.dropdown summary`, the value fields of `drawer_radio` and `drawer_select`, `select_fieldset`, `switch`) follow through the tokens and element rules (R13). `AppShell` doesn't render `data-hx-design="canvas"` and doesn't load `themes/canvas.css`, so none of the rules or tokens reach it (R14).

**Sample (R15).** `samples/canvas_layout/forms.py` (new) with a router included in `main.py`, like `navigation.py`; a link in the overview list `_modes()`. The page has three parts: a case form (`DataForm` of a Pydantic model with case number, client number, client name, status, date of receipt, note, priority) in a card; a states grid of plain controls (`form_field` with `aria-invalid`, `readonly`, `disabled`, checkboxes, radios, switches, buttons); and a split layout with a compact correction form in the aside. Test: `tests/samples/canvas_layout/test_forms.py` renders the page through the app's test client and checks for the form and the state controls.

**Screenshots (R17).** Taken with Playwright from the sample app before (on `main`) and after (on the branch), committed to a separate branch `design/canvas-form-controls-screenshots` (as for T-003) and linked in the pull request description by commit-pinned raw URLs, so the images don't land on `main`.

## Alternatives considered

- **Set `--hx-color-primary` and `--hx-color-secondary` to the text colour in the canvas theme:** one line instead of several rules, but it also turns links, tabs of the page header, metric tiles, bubbles, notifications and the slider black; that is a redesign of the canvas design, not of its forms.
- **Put all rules into `page-templates/canvas-shell.css`:** keeps everything in one file, but ties the look to the template instead of the design, and breaks the existing pattern (`[data-hx-design="canvas"]` in component stylesheets) that cards and pills follow.
- **New design-neutral tokens (`--hx-control-height`, `--hx-control-border-color`, …) with defaults for all designs:** a larger, speculative API; every default would have to reproduce Pico exactly to keep R14.
- **`neutral-400` (`#A1A1A1`) as border:** an existing token, but only 2.58:1 against white; it fails R2.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| No change of the public Python API; `feat:` | R13; only CSS and the sample change |
| `AppShell` and the default theme render exactly as before | R14; scoping by `data-hx-design="canvas"`; screenshot of R17 |
| WCAG 2.2 AA 1.4.11 (3:1) | R2, R3, R4, R6 |
| WCAG 2.2 AA 1.4.3 (4.5:1) | R7, R8 (`danger-700`, `neutral-500` 4.74:1, `neutral-700`) |
| CSS authoring conventions, no dependency, no JavaScript | Design: tokens in the `:root`-only theme, rules in the `pyhx` layer, concentric property order |
| `poe check` and `poe docs-build` pass | Plan: last step |

## Open questions

The developer asked to take the change to the final pull request without stopping; the proposals below were taken as decided and are listed in the pull request for review.

### Q1 Size of field labels

**Proposal:** 14 px (`--hx-text-item`, medium, `neutral-700`) instead of the 13 px of the design draft: an existing role, no new size, and the same size as the labels of the reference design.

**Answer:** Proposal taken (see above).

### Q2 Segment control

**Proposal:** Included (R12): it is offered as a control of `form_field`, and a blue segment control next to black buttons would break the neutral accent.

**Answer:** Proposal taken (see above).

### Q3 Where screenshots live

**Proposal:** On a separate branch, linked by commit-pinned URLs, as for T-003; nothing binary lands on `main`.

**Answer:** Proposal taken (see above).

## Areas of concern

1. **Pico's state rules** (R1–R6): the `pyhx` layer beats Pico, so a border set for hover or focus could hide Pico's error border or its validation icons. Handled by restating the error state in the same rules and checking every state in the states grid of R15. Owner: implementer.
2. **Default design unchanged** (R14): a rule without the canvas scope would change every app. Handled by scoping every new rule, and by comparing screenshots of the components sample (`AppShell`) before and after. Owner: implementer.
3. **case-sight changes its look on update** (R13): its forms (login pages) change with the next pyhx release. Intended; checked when case-sight updates pyhx. Owner: developer.

## Out of scope

- A compact field size (32 px) for asides: no size API for fields exists; the aside sample uses the default size. A later change if needed.
- The look of the default design and of the plain design.
- File dropzone, WYSIWYG editor, slider and tag inputs: own components with their own styles.
- Dark mode of the canvas design (it has none).
- Changes in case-sight.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** The canvas theme also lowers `--pico-form-element-disabled-opacity` to 0.5 (pyhx default 0.8): disabled checkboxes, radios, switches, fieldsets and buttons keep Pico's opacity, and at 0.8 they were hardly distinguishable from enabled ones (R5).
- **D2** After review, `segment_control` also takes the look of the other controls in the canvas design (beyond R12): white, the 3:1 field border, 8px radius, the same 6px below its label; before, its grey track (#EEEEEE, 1.16:1 on white) had no visible edge and an older rule placed it 2px higher than a field next to it.
- **D3** After review, a `dropdown` with a chosen value shows it in the text colour (Pico shows the summary in the placeholder colour either way), detected with `:has(:checked)`.
- **F1** Pico sets `--pico-outline-width` (text controls) and `--pico-border-width` (checkboxes, radios, switches) on the element, and gives selects no height formula; `pyhx/elements/form.css` sets them in the canvas scope.
- **F2** The solid button's hover darkens by 12 %, which shows no change on near-black; the canvas primary button lightens to `neutral-700` on hover instead.
- **F3** Checkbox and radio option labels are `<label>`s with an input inside, and so are the options of `segment_control`; the rule for option labels excludes `.hx-segment-control__option`.
- **F4** The `AppShell` forms page of `samples/components` renders pixel-identical before and after (R14); the only differing rows are the footer, which shows the commit hash.
- **F5** Not part of this change, seen while testing: Pico stretches `button(..., type="submit")` to full width outside `DataForm` (the sample sets `width: auto`); the outline and ghost variants of neutral buttons have a `neutral-400` border (2.58:1), which 1.4.11 doesn't require for buttons with a text label; the header of `samples/canvas_layout` overflows at phone width on every page.
- **F6** The screenshots of the forms page of `samples/canvas_layout` are kept in `screenshots/` next to this spec: [before](screenshots/canvas-shell--forms--before.png) (Pico defaults), [desktop](screenshots/canvas-shell--forms--desktop.png) and [phone](screenshots/canvas-shell--forms--phone.png) after the change, and the [segment control next to a dropdown](screenshots/canvas-shell--segment-and-dropdown.png) after the review (D2, D3). The `AppShell` comparison of F4 is not kept: a full-page image of the components sample adds nothing to the statement.

Rollout: pull request #23, released with the next minor version of `pyhx` (`feat:`). Apps on the canvas design (case-sight) get the new look when they update `pyhx`.

Open after this change: the points of F5, if wanted as their own changes (owner: developer); checking case-sight's login forms after its `pyhx` update (owner: developer).
