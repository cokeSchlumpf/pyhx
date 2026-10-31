# 2026-05-14 Use NumPy-style docstrings for Python code

- **Status:** Accepted
- **Deciders:** Michael Wellner

## Context

The codebase had no consistent docstring convention. Python supports several mainstream styles (Google, NumPy, reStructuredText/Sphinx), all of which are understood by Sphinx via `napoleon` and enforceable by linters like `pydocstyle` or `ruff`. Picking one now — before docstring coverage grows — avoids a future mass rewrite and keeps generated documentation uniform. Type information is already carried by annotations, so the chosen style only needs to express *prose* well.

## Decision

All Python docstrings in this repository use the **NumPy** style: section headers (`Parameters`, `Returns`, `Raises`, `Attributes`, `Examples`) underlined with dashes, and parameters listed as `name : type` with the description indented on the next line. Type fields are optional when fully redundant with annotations.

## Consequences

- **Positive:** uniform rendering in Sphinx (with `napoleon`); good readability for APIs with many parameters; aligns with the scientific-Python ecosystem we frequently borrow patterns from (NumPy, pandas, scikit-learn).
- **Negative:** more vertical space than Google style; slightly more verbose for short methods with one or two parameters.
- **Follow-ups:** enable `pydocstyle` / `ruff` `D` rules with the `numpy` convention to enforce going forward; convert existing docstrings opportunistically rather than in a single sweep.

## Options Considered

### A. NumPy
Section headers underlined with dashes; one parameter per block with type and indented description.
- **Pros:** very readable for long signatures; well supported by `napoleon`; matches the conventions of the libraries we most often look at for reference.
- **Cons:** verbose for trivial methods.

### B. Google
Indented section headers (`Args:`, `Returns:`, `Raises:`) with one-line parameter entries.
- **Pros:** terse; reads well for small APIs; widely used in modern projects.
- **Cons:** denser one-line entries become hard to scan once parameters carry longer descriptions.
- **Why not chosen:** the codebase will accumulate APIs with many parameters and longer prose; NumPy's per-parameter blocks scale better.

### C. reStructuredText / Sphinx classic
Inline `:param:` / `:returns:` / `:raises:` field tags.
- **Pros:** native to Sphinx, no extension required.
- **Cons:** noisy in source; harder to read as plain text in editors and on GitHub.
- **Why not chosen:** source readability matters more than skipping the `napoleon` extension.

## Related
- Implemented first in: `src/pyhx/core/types/path_template.py`
