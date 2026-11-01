# T-002 Upgrade to Python 3.14: plan

## Findings while planning

- **F1** A trial lock in a scratch copy of `pyproject.toml` and `poetry.lock` (floor `>=3.14`, commons on `versions/1`, without the direct `typing-extensions`) changes exactly one locked package: commons 0.2.1 → 1.1.0. sqlmodel, sqlalchemy, pandas and `typing-extensions` keep their versions, so concern 2 of the spec reduces to commons itself.
- **F2** Between commons `versions/0` and `versions/1`, the modules PyHX imports (`users`, `users.login_tokens`, `settings`, `string_operators`, `dict_operators`, `path_operators`, `datetime_operators`) change only in how ids are created (`new_id()`); no signature PyHX uses changes.
- **F3** Raising the floor alone makes `poe check` fail (ruff's 63 findings and 4 files to reformat, spec Design), so the floor, the dependencies and the lint fixes go into one step. CI comes first: pushed with the floor raised while CI still runs 3.12, the check would fail.
- **F4** The tests don't check the version or format of sample record ids (no `uuid` in `tests/samples`), so R7 is proven by the sample tests passing and by a test that `Project().id` is a UUID v7.

Deviations from the spec:

- None.

## Branching

Branch `feature/upgrade-to-python-3-14`, draft PR #10 (`feat!: Upgrade to Python 3.14 and commons 1.x`). Implementation pauses for a review after each step; each step is its own commit ending in `(T-002)`.

## Steps

### 1. CI on Python 3.14

- `.github/workflows/check.yml` and `docs.yml`: `with: python-version: "3.14"`, as in commons. **R5**
- Proof: after the push, the check of PR #10 runs on Python 3.14 (job log) and passes with the current code (its floor `>=3.12` allows 3.14).

### 2. Python 3.14 and commons 1.x

- `pyproject.toml`: `requires-python = ">=3.14, <4.0"`, commons on `branch = "versions/1"`, the direct dependency `typing-extensions` removed; `poetry lock` and `poetry install` (commons 1.1.0). **R1, R2, R3**
- `components/data/data_section.py`: `TypeVar` from `typing`, the 3.12 comment removed. **R3**
- `poetry run poe fix` for the remaining ruff findings (UP037) and the formatter (PEP 758 `except`), each file's diff reviewed by hand; nothing beyond what ruff reports. **R4**
- Proof: `poetry check --lock`; `poetry show commons` shows 1.1.0; `grep typing_extensions src/pyhx` finds nothing; `poetry run poe check` passes (lint, format, mypy, all tests including the samples).

### 3. Docs and sample ids

- `docs/getting-started/installation.md`: Python **3.14** or newer. **R6**
- `samples/app_shell_layout/pages/data_page.py`: `Project.id` from `new_id()` of commons, docstring updated. **R7**
- A test in `tests/samples` that a new `Project` gets a UUID v7 id. **R7**
- Proof: `poetry run poe docs-build` passes; `poetry run poe check` passes with the new test.

### Release (at close-out)

- `close-change` publishes PR #10 with the title `feat!: Upgrade to Python 3.14 and commons 1.x` and a `## Migration` section from the spec's Design. **R8**
- Proof: the PR's title check passes; the Release PR afterwards proposes 0.4.0 with the change under breaking changes.

## Risks

- **Unquoted annotations break at runtime:** the full test suite in step 2 builds the models and starts the samples; a failure means restoring the quotes in that place and recording it as a finding.
- **CI on 3.14 fails for setup reasons:** step 1 is its own commit, so a failure is isolated; commons runs the same workflows on 3.14.
- **Release-please skips the breaking marker:** the squash commit message must be the PR title with a short body (see the release PR check before merging it).

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 2: `poetry check --lock`, `poe check` |
| R2 | Step 2: `poetry show commons` (1.1.0), `poe check` |
| R3 | Step 2: grep, `pyproject.toml` diff, `poe check` |
| R4 | Step 2: `poe check` |
| R5 | Step 1: PR #10's check on 3.14 |
| R6 | Step 3: `poe docs-build`, diff |
| R7 | Step 3: new sample test, `poe check` |
| R8 | Close-out: PR title check, Release PR 0.4.0 |
