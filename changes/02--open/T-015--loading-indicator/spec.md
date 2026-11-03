# T-015 Loading indicator: spec

## Requirements

### The component

- **R1** `c.loading_indicator(*, label: str, kind="spinner", appearance="primary", size="md", **kwargs)` is exported from `pyhx.components`, with the type `LoadingIndicatorKind = Literal["spinner", "ripple", "pulse", "dots", "bars"]`; `kwargs` go to its root element.
- **R2** It renders one inline element with `role="status"` and `aria-label` set to `label`, and no visible text; it never carries `aria-busy`.
- **R3** Five kinds, as in the reviewed draft: `spinner` (a turning arc on a faint ring), `ripple` (a solid dot sending out a ring), `pulse` (a dot that breathes), `dots` (three dots lighting up in turn) and `bars` (three bars rising and falling). The default is `spinner`.
- **R4** `appearance` takes the shared `Appearance` values (the colours of pill and progress bar); `primary` is the theme's primary colour, in the canvas design its text colour. Inside a solid button the mark takes the button's text colour, and the spinner's ring stays visible on the solid background.
- **R5** `size` `sm`, `md`, `lg` sizes the mark to sit on a text line: `sm` next to 12–13px text and in table rows, `md` next to body text and pills, `lg` next to headings. The mark is vertically centred on the line it stands in, within 1px: beside a label in a flex row, beside a button's label, inside a pill before its text, in a table cell and after a link's text in a navigation.
- **R6** With `prefers-reduced-motion: reduce` nothing moves and the mark stays visible: pulse is a solid dot, ripple has no ring, the spinner shows a static half arc, dots and bars stand at a middle step.
- **R7** Pico's global rules don't change it (no Pico spinner, no Pico background or spacing on its parts).
- **R8** It looks as in the reviewed draft in the plain design (`AppShell`) and the canvas design (`CanvasShell`), at desktop and phone width, needs no JavaScript and adds no text of its own.

### Samples, docs and tests

- **R9** The components sample (`AppShell`) has a page `/loading-indicator` with every kind, size and appearance, the reduced-motion note, when to use which kind, and the in-use examples (a header with a pill, the mark beside and inside a pill, a button with the mark beside its label, a solid button with a spinner, table rows, navigation), each with its code, linked from its home page; the canvas layout sample (`CanvasShell`) shows the same page at `/loading-indicators`.
- **R10** The module docstring documents the component and when to use which kind.
- **R11** Unit tests cover R1–R4 and R6–R7 (markup, role and label, no `aria-busy`, classes per kind, size and appearance, the reduced-motion rules, the rule for solid buttons); sample tests cover R9; `poetry run poe check` and `poetry run poe docs-build` pass.

## Design

```
<span class="hx-loading-indicator hx-loading-indicator--spinner hx-loading-indicator--primary hx-loading-indicator--md" role="status" aria-label="Saving">
  <span class="hx-loading-indicator__part"></span>     three parts, shown only by dots and bars
  <span class="hx-loading-indicator__part"></span>
  <span class="hx-loading-indicator__part"></span>
</span>
```

- **Module** `src/pyhx/components/primitives/loading_indicator.py`, a `@component` like `progress_bar`, exported from `primitives/__init__.py` and `components/__init__.py` with its kind type. The parts are `span`s (not the draft's `i`), and are rendered only for `dots` and `bars`.
- **CSS** `src/pyhx/static/css/pyhx/components/primitives/loading-indicator.css`, imported in `pyhx.css` (layer `pyhx`), in the structure of `progress-bar.css`: tokens on the root (`--loading-indicator--color` per appearance; `--loading-indicator--dot` and `--loading-indicator--box` per size: 6/12, 8/16, 12/24 px as in the draft; `--loading-indicator--track` = `color-mix(in srgb, currentColor 15%, transparent)`), the kinds with the draft's keyframes renamed `hx-loading-indicator-*`, appearances, sizes, a `prefers-reduced-motion` block with the specificity of the motion rules, and a canvas block (`primary` is `--hx-color-text`, `neutral` `--hx-color-neutral-500`).
- **Centring:** the root is `display: inline-flex; align-items: center; vertical-align: middle; flex: none`, so it centres in a flex row by `align-items` and in running text by `vertical-align`. The ripple's ring is an absolutely positioned `::after` and doesn't take space.
- **Spinner ring:** the ring is `--loading-indicator--track`, derived from the mark's own colour, so it is faint on light backgrounds and stays visible in white on a solid one. `.hx-button--solid .hx-loading-indicator` sets the colour to the button's text colour (`currentColor`), at a specificity above the appearance rules.
- **In a pill:** `.hx-pill__label` is a flex row without a gap; `.hx-pill__label:has(> .hx-loading-indicator)` gets a small gap, so `c.pill([c.loading_indicator(...), "Import 35 %"])` works without a change to `pill`.
- **Pico:** the component sets `box-sizing` and `background` itself and uses neither `aria-busy` nor elements Pico styles (`i`, `a`, `button`).
- **Samples:** `samples/components/pages/loading_indicator.py` (router, page, `showcase()` with `# docs:` regions), `samples/canvas_layout/loading.py` renders `showcase()` in the canvas design; both home pages link it.

## Alternatives considered

- **An SVG per kind:** sharper arcs, but five inline SVGs with SMIL or CSS animation are more markup and harder to colour per appearance and to stop under reduced motion; the draft's CSS shapes do the job.
- **Pico's `aria-busy` spinner:** one kind, its own colour and size, and `aria-busy` says the element's content is incomplete, not "this runs"; `role="status"` with a label is what screen readers announce.
- **A `spinner` option on `c.button` and an indicator slot on `c.pill`:** more API in two components for what composition does already; the intent excludes changes to them.
- **A colour `inherit` among the appearances:** only needed in a solid button, which the button rule covers.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Additive, non-breaking | R1 (new export only) |
| CSS conventions, structure of `progress_bar` | R8, design "CSS" |
| Pico's global rules don't reach it | R2, R7 |
| Accessible: label required, reduced motion | R1, R2, R6 |
| No JavaScript, no dependency, server-rendered | R8 |
| Public repository | samples and screenshots use made-up content only |
| Both page templates | R8, R9 |
| Drafts reviewed, then up to the published PR | process, plan |

## Open questions

None. The developer reviewed the design drafts and waived the acceptance stops up to the published PR. The default kind (`spinner`) and the API were proposals of the brief: Proposal accepted (autonomous run).

## Areas of concern

1. **Motion in many rows at once** (R3): a list with many moving marks is restless; the docs recommend `pulse` for dense lists, and finished rows render none. Owner: the app's developer.
2. **Centring in running text** (R5): `vertical-align: middle` centres on the x-height, not exactly on the line box; checked by measuring in both designs. Owner: Claude.
3. **`color-mix` with `currentColor`:** supported by current browsers (the settings menu uses it already). Owner: Claude.

## Out of scope

- No docs page lists the components (T-013, F4): the samples and the module docstring are the reference, so no guide page is added.
- A progress value, a text of its own, changes to `c.button`, `c.pill` or the navigation.
