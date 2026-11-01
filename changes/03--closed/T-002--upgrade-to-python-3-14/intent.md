# T-002 Upgrade to Python 3.14

## Problem

We need to keep our Python versions up to date, and we want to use UUID v7 (`uuid.uuid7()`, in the standard library since Python 3.14) where record ids are created. PyHX still declares Python `>=3.12`, its CI checks and builds the docs on 3.12 (the default of the shared workflows of core--devops-workflows), and its installation guide names 3.12 as the minimum. That floor is already wrong: commons, which PyHX depends on, requires `>=3.14`, so PyHX can't be installed on 3.12 or 3.13 anyway.

## Proposed outcome

- PyHX requires Python `>=3.14, <4.0`.
- CI checks, docs builds and releases run on Python 3.14, as in commons.
- The documentation names Python 3.14 as the minimum.
- Where PyHX code creates record ids (today only the sample `samples/app_shell_layout/pages/data_page.py`), they are UUID v7.
- It doesn't change DOM element ids in the components: they only need to be unique, so they stay `uuid4`.
- It doesn't change commons, which is migrated to UUID v7 separately.

## Affected users and systems

- **PyHX (library):** the Python floor in `pyproject.toml`; code and lint settings may pick up 3.14 idioms.
- **CI (`.github/workflows/`):** the check, docs and release callers pass Python 3.14 to the shared workflows.
- **Documentation:** installation guide.
- **Samples:** record ids in the app shell sample.
- **Apps on PyHX:** nothing changes for them in practice, as commons already requires 3.14.

## Constraints

- Released as `feat:` (a minor version), not `feat!`: the floor PyHX declares only catches up with what commons already enforces.
- core--devops-workflows and commons stay unchanged.
- The public API of PyHX stays unchanged.
- PyHX's code adopts 3.14 idioms only where the linters ask for them once the floor is 3.14; no wider modernisation. `poe check` is clean afterwards.

## Open questions

None.
