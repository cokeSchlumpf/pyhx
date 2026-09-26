# 2026-05-27 CSS authoring conventions

- **Status:** Accepted
- **Deciders:** Michael Wellner

> **Note (2026-09-26):** During the PyHX rebrand the two original namespaces — `k-` for design tokens and `kx-` for component classes — were unified into a single `hx-` namespace (`--hx-*` tokens, `.hx-*` BEM classes), and the `kx` DSL proxy and `data-kx-*` attributes became `hx` / `data-hx-*`. The KPMG default theme was replaced by a neutral PyHX theme; corporate branding now ships as an optional `:root`-only override. The text below reflects the current convention.

## Context

The library ships CSS in several files (`reset.css`, `theme.css`, per-template files under `page-templates/`) and will keep growing as more templates and components land. Without a written convention the files will drift in naming, structure, property order, and commenting. The surface is still small — fixing the conventions now is the cheapest moment to do it. The decisions also feed any future Stylelint configuration.

## Decision

All hand-written CSS in this repository follows the conventions below.

### 1. Naming

- **Theme tokens** (cross-template scales / contracts): custom properties prefixed `--hx-`, grouped by category (`--hx-color-*`, `--hx-spacing-*`, `--hx-z-*`, `--hx-transition-*`, …). Live in `theme.css`. Used by any template that needs to coordinate with the rest of the design system.
- **Template-local custom properties** (dimensions of *this* template only): `--{name}--{modifier}` style, e.g. `--nav-main--width`, `--header--height`. No `--hx-` prefix. Live in the template's own file.
- **Component classes**: BEM, with `hx-` as the project namespace. Block is the component (`hx-menu`), element is `hx-menu__button`, modifier — when needed — is `hx-menu--collapsed`. Modifiers are avoided in favour of state attributes where possible (see §4).
- **One namespace:** tokens and component classes share the `hx-` prefix; the leading `--` (custom property) vs `.` (class) already tells them apart. This does not clash with HTMX's `hx-*` *attributes* (`hx-get`, `hx-swap`, …): ours are class names and custom properties, which live in separate namespaces from HTML attributes.
- **Utility classes** that map to a token follow the token name, e.g. `.font-heading` → `var(--hx-font-heading)`.

### 2. File organization & cascade layers

CSS is organized around three named cascade layers, declared once at the top of `pyhx.css`:

```css
@layer pico, pyhx, templates;
```

Layer order is priority order: rules in `templates` beat rules in `pyhx`; rules in `pyhx` beat rules in `pico`. Our overrides win by **layer**, not by specificity — so Pico's element-level selectors (and any other third-party CSS) stop forcing us into specificity wars.

**What goes in each layer:**

- **`pico`** — third-party framework (Pico CSS). Imported from `pyhx.css` with `@import "./pico.min.css" layer(pico)`.
- **`pyhx`** — design system: reset, theme tokens, and (future) reusable cross-template components such as buttons, form controls, cards. Imported from `pyhx.css` with `@import "./pyhx/<file>.css" layer(pyhx)`.
- **`templates`** — per-page-template layout and arrangement. Each template has its own stylesheet at `page-templates/<template>.css`, which wraps its content in `@layer templates { … }` so it joins the templates layer when loaded via `<link>`.

**File structure:**

```
css/
├── pyhx.css                       ← entry; declares layers; loads pico + pyhx
├── pyhx/
│   ├── reset.css                  (pyhx layer, via @import)
│   └── theme.css                  (pyhx layer, via @import — neutral PyHX default theme)
└── page-templates/
    └── <template>.css             (templates layer, via @layer wrapper)
```

**Loading per page** is set in each page template's `Skeleton(stylesheets=...)`:

1. `/static/css/pyhx.css` — always.
2. `/static/css/page-templates/<template>.css` — the template the page uses.
3. *(optional)* `/static/themes/<brand>.css` — branding override (see §10).

**Per-template files**: contain *only* that template's rules; wrap content in `@layer templates { … }`; do not re-declare the layer order (it's established by `pyhx.css`, which always loads first); scope rules to their `body[data-hx-page-template="…"]` selector (still useful for isolation between page templates even though layer ordering already handles specificity).

### 3. Section order within a template file

Sections always appear in the same canonical order, each introduced by a one-line marker `/* --- Section name --- */`:

1. **Tokens** — template-local custom properties.
2. **Layout** — grid / regions / structural rules.
3. **Components** — buttons, drawers, etc. (one section per component if multiple).
4. **Mode variants** — `&[data-hx-mode="…"]` overrides.
5. **Responsive** — `@media` query blocks. Mobile / breakpoint variants live last.

### 4. State via attributes and `:has()`, not modifier classes

State is expressed by data attributes (`data-hx-mode`, `data-hx-menu-open`, etc.) or by `:has()` against a real form element, **not** by toggling modifier classes from JavaScript. Rationale: keeps HTML semantic and free of presentation-only classes, lets CSS-only toggles work, and keeps state visible in DevTools as a real value.

### 5. Property order within a rule (concentric / outside-in)

Properties are grouped and ordered as: **Position → Layout → Box → Typography → Visual → Motion → Interaction**. Only the categories present in a rule appear. Each present group is preceded by a one-line label using the same vocabulary:

```css
.example {
    /* Position */
    position: sticky;
    top: 0;

    /* Layout */
    display: flex;
    align-items: center;

    /* Box */
    height: 3rem;
    padding: 0;

    /* Visual */
    background-color: var(--hx-color-overlay-light);

    /* Motion */
    transition: opacity var(--hx-transition-slow);

    /* Interaction */
    pointer-events: auto;
}
```

Within a group, properties follow natural concentric reading (e.g., `position` first, then offsets `top/right/bottom/left`, then `z-index`). Strict alphabetical sort *within* groups is not required — it adds friction without payoff unless enforced by tooling (see §9).

#### 5.1 Property reference

Non-exhaustive list of common CSS properties and the group they belong to. When a property could fit multiple groups, the spec prefix decides (`text-*` → Typography, `background-*` → Visual, `border-*` → Box).

**Position**
- `position`, `top`, `right`, `bottom`, `left`, `inset`, `inset-block`, `inset-inline`
- `z-index`

**Layout**
- `display`
- Grid: `grid`, `grid-template`, `grid-template-columns/rows/areas`, `grid-area`, `grid-column`, `grid-row`, `gap`, `row-gap`, `column-gap`
- Flex: `flex`, `flex-direction`, `flex-wrap`, `flex-grow`, `flex-shrink`, `flex-basis`, `order`
- Alignment: `align-items`, `align-content`, `align-self`, `justify-items`, `justify-content`, `justify-self`, `place-items`, `place-content`, `place-self`
- Flow: `float`, `clear`
- Multi-column: `columns`, `column-count`, `column-width`, `column-rule`

**Box**
- Sizing: `width`, `height`, `min-width`, `min-height`, `max-width`, `max-height`, `aspect-ratio`, `box-sizing`
- Spacing: `padding`, `padding-top/right/bottom/left`, `padding-inline`, `padding-block`, `margin`, `margin-top/right/bottom/left`, `margin-inline`, `margin-block`
- Border: `border`, `border-top/right/bottom/left`, `border-width`, `border-style`, `border-color`, `border-radius`, `border-image`
- Outline (treated like border): `outline`, `outline-width`, `outline-style`, `outline-color`, `outline-offset`
- Overflow: `overflow`, `overflow-x`, `overflow-y`, `overflow-clip-margin`

**Typography**
- Font: `font`, `font-family`, `font-size`, `font-weight`, `font-style`, `font-variant`, `font-feature-settings`
- Text: `text-align`, `text-decoration`, `text-transform`, `text-indent`, `text-overflow`, `text-shadow`
- Spacing: `line-height`, `letter-spacing`, `word-spacing`
- Wrapping: `white-space`, `word-break`, `overflow-wrap`, `hyphens`
- Color: `color` (text only — `background-color` is Visual)
- Writing: `writing-mode`, `direction`

**Visual**
- Background: `background`, `background-color`, `background-image`, `background-position`, `background-size`, `background-repeat`, `background-attachment`, `background-clip`, `background-origin`
- Effects: `box-shadow`, `opacity`, `filter`, `backdrop-filter`
- Clipping / Masking: `clip`, `clip-path`, `mask`, `mask-image`
- Blending: `mix-blend-mode`, `background-blend-mode`, `isolation`
- `visibility`

**Motion**
- Transform: `transform`, `transform-origin`, `transform-style`, `perspective`, `perspective-origin`, `backface-visibility`
- Transition: `transition`, `transition-property`, `transition-duration`, `transition-timing-function`, `transition-delay`
- Animation: `animation`, `animation-name`, `animation-duration`, `animation-timing-function`, `animation-delay`, `animation-iteration-count`, `animation-direction`, `animation-fill-mode`, `animation-play-state`
- `will-change`

**Interaction**
- `cursor`
- `pointer-events`
- `user-select`
- `touch-action`
- `caret-color`
- `resize`
- `appearance`
- `accent-color`
- Scrolling: `scroll-behavior`, `scroll-snap-type`, `scroll-snap-align`, `scroll-margin`, `scroll-padding`

**Edge cases worth knowing:**
- `text-shadow` is Typography, `box-shadow` is Visual — both shadows, but the spec prefix decides.
- `color` is Typography (sets text colour); `background-color` is Visual.
- `outline-*` is grouped with `border-*` under Box even though outline doesn't take space — treating border-like properties together keeps the rule "all `*-width/style/color` for box edges → Box."
- `visibility` is Visual (controls rendering), not Layout — `visibility: hidden` still reserves space, unlike `display: none`.
- Custom properties (`--my-var`) are not grouped — they live in the **Tokens** section at the top of a rule (or in the file's `/* --- Tokens --- */` section), above any standard properties.

### 6. Nesting

CSS nesting is used **only** for things BEM names don't already express:

- Page-template scope (`body[data-hx-page-template="app-shell"] { … }`)
- Variant of the scope (`&[data-hx-mode="app"] { … }`)
- State (`&:has(#hx-menu__toggle:checked) { … }`)
- Breakpoints (`@media (max-width: 767px) { … }`)

BEM elements are **not** nested inside their block (`.hx-menu { .hx-menu__button {…} }` is forbidden — the relationship is already in the name; nesting double-encodes it and inflates specificity).

### 7. Tokens over literals

**At use sites:** if a value belongs to a theme scale (color, spacing, type, z-index, transition, blur, shadow), use the token directly. Literals are only acceptable for one-off layout values specific to a template (sidebar width, region heights). Debug / placeholder colors carry an explanatory comment.

**Defining template-local custom properties** (`--name--modifier` style, declared in a template file's `--- Tokens ---` section) is justified only if at least one of these is true:

1. **The value is not in `theme.css`** — typically a layout dimension specific to this template (`--header--height: 3rem`, `--drawer--width: 360px`, `--footer--height: 2rem`).
2. **The value is reused in multiple rules** within the template (DRY pays off).

Otherwise: inline the value directly at the call site. This applies to:

- Single-use single-token aliases (`--drawer--bg: var(--hx-color-neutral-150)` used in only one rule). Inline the theme token.
- Single-use composite expressions combining multiple theme tokens (`--header--bg: linear-gradient(150deg, var(--hx-color-purple) 30%, var(--hx-color-primary) 100%)`). Even though the value is longer, inlining it at the only use site is more honest than introducing a documentation-only indirection. If the composite is ever reused, *that's* the moment to extract a token (Case 2).

### 8. Accessibility baseline

Every template file honours `prefers-reduced-motion: reduce` for any transitions or animations it declares. Visually hidden interactive elements remain keyboard-focusable — never use `display: none` or the `hidden` attribute for elements that participate in keyboard navigation.

### 9. Tooling

Conventions are currently enforced by review, not tooling. The expected next step is Stylelint with `stylelint-order` (property order) and a BEM-naming plugin. Adopting Stylelint is the trigger for switching property order to "alphabetical within concentric groups," since at that point the linter does the work.

### 10. Theming

Branding/theming is done by overriding **theme tokens** on `:root`. An override stylesheet contains only `:root { … }` declarations and is loaded after `pyhx.css` as a separate `<link>`:

```html
<link rel="stylesheet" href="/static/css/pyhx.css">
<link rel="stylesheet" href="/static/themes/corporate.css">       <!-- optional override -->
<link rel="stylesheet" href="/static/css/page-templates/app-shell.css">
```

```css
/* themes/corporate.css */
:root {
    --hx-color-primary: #E60000;
    --hx-color-purple:  #FF0099;
}
```

The override file is **unlayered**. Unlayered styles sit in an implicit final layer that beats every named layer, so the override automatically wins over `theme.css` (which is in `pyhx`). Custom properties propagate through inheritance: every `var(--hx-color-primary)` reference, in any layer, resolves to the override's value.

**Constraint:** theme override files **must contain only `:root` rules**. Any non-`:root` rule in an override file is unlayered too and would win over the entire framework — a silent foot-gun. For defense-in-depth, an override can wrap in `@layer pyhx { :root { … } }`: tokens still propagate correctly (custom properties don't care about layers), but any accidental non-`:root` rule is bounded to the `pyhx` layer.

**The neutral PyHX theme** lives in `pyhx/theme.css`, ships with the library, and is the default. Brand themes (e.g. a corporate theme) are `:root`-only override stylesheets linked after `pyhx.css`, as shown above; a consuming project loads one only if it needs to deviate from the PyHX default.

## Consequences

- **Positive:**
  - One vocabulary across naming, sections, and property labels — a reader scanning any CSS file knows what every block is.
  - Cascade layers eliminate specificity wars with Pico (and any future third-party CSS) — our rules win by layer order, not by selector arms race.
  - Specificity stays predictable (single-class selectors via BEM; nesting only adds scope/state, not depth).
  - Token-first encourages design-system reuse and makes theme tweaks cheap.
  - Theming is a single-file drop-in: a project deviates from the PyHX default by adding one `<link>` to a `:root`-only override stylesheet — no library changes.
  - A11y baseline (reduced motion, focusable hidden state-holders) is part of the convention, not an afterthought.
- **Negative:**
  - Comment-heavy: every property block carries a category label, which is noisy in single-property rules.
  - BEM class names are verbose compared to utility-first or unscoped naming.
  - The strict section / property ordering adds friction in casual edits until tooling enforces it.
  - Per-page CSS is split across two `<link>` tags (`pyhx.css` + template). Minor first-load sequencing cost; addressable by bundling in production builds.
  - Theme override files carry an implicit convention ("only `:root` rules") that is documented in §10 but enforceable only by review.
- **Follow-ups:**
  - Add Stylelint configuration covering property order and BEM class names (see §9).
  - Decide whether the "label every block, even single-property" rule should be relaxed to "label only rules with 2+ groups" once the codebase grows.
  - When a component is needed by a second page template, extract it from the `templates` layer into `pyhx/components/` to become reusable across templates.

## Options Considered

### A. BEM with `hx-` namespace (chosen)
`.hx-menu`, `.hx-menu__button`, `.hx-menu--open`.
- **Pros:** explicit block/element/modifier relationship; flat specificity; survives refactors well; widely understood.
- **Cons:** verbose class names; nested-DOM purity sometimes impractical (see §6 deviation for the state-holder + label pattern).

### B. Atomic / utility-first (Tailwind-style)
Compose styles from many tiny classes in markup.
- **Pros:** tiny stylesheet that doesn't grow with new components; no naming debates.
- **Cons:** requires deep design-system buy-in and a build pipeline; dense markup; semantic meaning hides under utilities.
- **Why not chosen:** the project favours readable, semantic HTML and uses Pico CSS as a base — utility-first contradicts both.

### C. OOCSS / SMACSS
Older methodologies emphasising structure/skin separation and rule categorisation.
- **Pros:** historically influential; SMACSS's `.is-` state prefixes are useful.
- **Cons:** largely subsumed by BEM in modern practice.
- **Why not chosen:** BEM covers the same ground more explicitly.

### D. Property order: concentric / outside-in (chosen)
Position → Layout → Box → Typography → Visual → Motion → Interaction.
- **Pros:** reads as "where am I, how am I laid out, how big am I, what do I look like" — natural narrative.
- **Cons:** no mechanical enforcement without tooling.

### E. Property order: alphabetical
Strict alphabetical sort of every declaration.
- **Pros:** trivially enforceable by Stylelint; zero human judgement.
- **Cons:** `position` (the controlling property) sorts to the middle of the position group, hiding the property whose value defines what `top/right/bottom/left/z-index` even mean.
- **Why not chosen:** without Stylelint enforcement the friction outweighs the benefit; revisit when Stylelint is adopted (see §9 follow-up).
