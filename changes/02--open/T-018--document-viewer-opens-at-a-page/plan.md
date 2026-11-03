# T-018 Document viewer opens at a page: plan

## Findings while planning

- **F1** `pyhx.canvas-shell.js` closes open `<details>` groups on a click outside and on Escape, returning focus to the summary; the switcher follows it.
- **F2** `_Toolbar` renders its controls inside the viewer's context, so `dv.files()` can be a context consumer like `pager()`.

Deviations from the spec:

- None yet.

## Branching

`feature/document-viewer-opens-at-a-page`, one pull request, squash-merged after the checks, then the Release PR (allowed by the developer for app--casesight T-014).

## Steps

### 1. Start position

- `start` and `selected`, server rendering and script. **R1–R4**
- Proof: tests of the rendered markup; the sample in a browser.

### 2. Document switcher

- `vm.DocumentLink`, `dv.files`, script, CSS, texts. **R5–R9**
- Proof: tests of the markup; the sample in a browser at desktop and phone width (filter, keys, outside click, Esc).

### 3. Guide and sample

- **R10**
- Proof: `poe check`, the sample page.

## Risks

- **Script initialised twice** (htmx swaps): `viewer(root)` is memoised per root; the start position runs only on creation.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1–R4 | Step 1 |
| R5–R9 | Step 2 |
| R10 | Step 3 |
