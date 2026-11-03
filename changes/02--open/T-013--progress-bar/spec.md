# T-013 Progress bar: spec

## Requirements

### The component

- **R1** `c.progress_bar(value, *, working=False, motion="sheen", label=None, value_text=None, supporting_text=None, appearance="primary", size="md", aria_label=None, **kwargs)` is exported from `pyhx.components`; `value` is a `Pct` or `None`.
- **R2** With a value, the filled part covers that fraction of the track. The track is the element with `role="progressbar"`, `aria-valuemin="0"`, `aria-valuemax="100"` and `aria-valuenow` (the value in percent, rounded); `aria-valuetext` is `value_text` when it is a string.
- **R3** The accessible name is `aria_label`, else `label` when it is a string; the component adds no text of its own.
- **R4** Modes: static (`working=False`, nothing moves); working (`working=True`): the filled part moves as chosen by `motion`: `"sheen"` (a light band sweeps across it), `"stripes"` (diagonal stripes run along it) or `"pulse"` (it fades in and out); waiting (`value=None`): no `aria-valuenow`, a segment travels along the track. Working and waiting bars carry `aria-busy="true"`.
- **R5** With `prefers-reduced-motion: reduce`, nothing moves; a waiting bar shows a faint full track.
- **R6** `label` and `value_text` are shown above the bar (label left, value right, tabular figures), `supporting_text` below it; without any of them the component renders the bar alone.
- **R7** `appearance` takes the shared `Appearance` values; the default `primary` is the theme's primary colour, in the canvas design its text colour; `size` `sm`, `md`, `lg` sets the bar's height (4, 8, 12 px).
- **R8** It looks as in the reviewed draft in the plain design (`AppShell`) and the canvas design (`CanvasShell`), works at phone width, needs no JavaScript, and forwards `kwargs` to its root element.

### Samples and tests

- **R9** The components sample (`AppShell`) has a page `/progress-bar` with every mode, motion, appearance and size and their code, linked from its home page; the canvas layout sample (`CanvasShell`) shows the same variants on a page `/progress-bars`.
- **R10** Unit tests cover R1–R7; `poetry run poe check` and `poetry run poe docs-build` pass.

## Design

```
<div class="hx-progress-bar hx-progress-bar--primary hx-progress-bar--md hx-progress-bar--working hx-progress-bar--sheen">
  <div class="hx-progress-bar__head">                       only with label or value_text
    <span class="hx-progress-bar__label">Analysing</span>
    <span class="hx-progress-bar__value">35 %</span>
  </div>
  <div class="hx-progress-bar__track" role="progressbar" aria-valuenow="35" … aria-busy="true">
    <div class="hx-progress-bar__fill" style="--hx-progress-bar--value: 35%"></div>
  </div>
  <div class="hx-progress-bar__supporting-text">Page 4 of 12 · about 3 min left</div>
</div>
```

- **Module** `src/pyhx/components/primitives/progress_bar.py`, a `@component` like `metric_tile`; types `ProgressMotion = Literal["sheen", "stripes", "pulse"]`. Waiting adds `hx-progress-bar--waiting` (and no `--working`/motion class).
- **CSS** `src/pyhx/static/css/pyhx/components/primitives/progress-bar.css`, imported in `pyhx.css` (layer `pyhx`), following the CSS authoring conventions: tokens on the root (`--hx-progress-bar--color` per appearance, `--hx-progress-bar--height` per size, `--hx-progress-bar--track-color: var(--hx-slider--track-color)`), keyframes `hx-progress-bar-sheen`, `-stripes`, `-pulse`, `-waiting` taken from the draft, a `prefers-reduced-motion` block, and a `[data-hx-design="canvas"]` block (primary is `--hx-color-text`, track `--hx-color-neutral-200`, Inter metrics of the draft).
- **Value in percent** from `Pct.percent`, rounded for `aria-valuenow`; the width is `str(pct)` (a CSS percentage).
- **Samples:** `samples/components/pages/progress_bar.py` (router, page, a function `showcase()` with the variants and `# docs:` regions shown with `snippets`); `samples/canvas_layout/progress.py` renders `showcase()` in the canvas design.

## Alternatives considered

- **The native `<progress>` element:** its parts are styled through browser-specific pseudo-elements (`::-webkit-progress-value`, `::-moz-progress-bar`), the indeterminate state can hardly be styled and animated alike in all browsers; a `div` with `role="progressbar"` renders the same everywhere.
- **A thumbless `c.slider`:** an input with pointer handling and form semantics, not a progress bar (intent).
- **One movement only:** the developer asked for all three as an option (intent Q3).

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Additive, non-breaking | R1 (new export only) |
| Design and CSS conventions, slider tokens, phone width | R7, R8, design "CSS" |
| Accessible | R2, R3, R4, R5 |
| No JavaScript, no new dependency, server-rendered | R8 |
| Texts translated | R3 (no own texts) |
| Both page templates | R8, R9 |
| Design draft reviewed, then up to the published PR | Process, plan |

## Open questions

None. The developer reviewed the design draft and waived the acceptance stops up to the published PR.

## Areas of concern

1. **Motion on many bars at once** (R4): a table with many working bars could be restless; the app chooses `pulse` or `working=False` there; the sample shows small bars in a list. Owner: Michael.
2. **Contrast of the fill on the track** (R7): `warning` and `neutral` fills against the light track are checked in the screenshots of both designs. Owner: Claude.

## Out of scope

- No docs page lists the components (the samples are their reference), so no guide is added; the T-011 guide uses the component in its sample.
- Steppers, circular progress, a value the user sets.
- Switching the T-011 sample to the component: done in T-011 after this change is merged.
