# T-002 Upgrade to Python 3.14: spec

## Requirements

### Package

- **R1** `pyproject.toml` declares `requires-python = ">=3.14, <4.0"`, and `poetry.lock` is consistent with it (`poetry check --lock` passes).
- **R2** PyHX references commons on `branch = "versions/1"` (locked at 1.1.0 or later), and everything PyHX uses of commons works unchanged (proved by `poe check`).
- **R3** No module of `src/pyhx` imports from `typing_extensions` for what `typing` offers on 3.14 (today: `TypeVar` with a default in `components/data/data_section.py`); the comment that justified it for 3.12 is gone, and `typing-extensions` is no longer a direct dependency in `pyproject.toml`.

### Code

- **R4** `poetry run poe check` passes with the 3.14 floor. Code changes are limited to what its ruff and mypy steps report for target 3.14; nothing else is modernised.

### CI

- **R5** The callers `.github/workflows/check.yml` and `.github/workflows/docs.yml` pass `python-version: "3.14"` to the shared workflows, as commons does; the check of this branch's PR runs on 3.14 and passes.

### Documentation

- **R6** `docs/getting-started/installation.md` names Python 3.14 as the minimum, and `poetry run poe docs-build` passes.

### Samples

- **R7** The app shell sample creates the ids of new records with `new_id()` of commons (`samples/app_shell_layout/pages/data_page.py`, `Project.id`), and its docstring says so; the sample tests pass.

### Release

- **R8** The PR is released as a breaking change: its title is `feat!: Upgrade to Python 3.14 and commons 1.x`, and its description has a `## Migration` section for apps on PyHX.

## Design

### Why the floor moves

PyHX uses commons on `versions/0`, which stays at 0.2.1 and still allows Python 3.12. commons 1.0.0 (`versions/1`) requires Python 3.14 and is otherwise unchanged in its public API; 1.1.0 adds `commons.id_operators.new_id()` (also exported from `commons.database`), which returns `str(uuid.uuid7())`, and uses it for commons' own ids. This change follows the migration of commons PR #18: raise `requires-python` (R1), reference `versions/1` (R2), pass `python-version: "3.14"` in CI (R5). `poetry update commons` after the branch change locks the new version.

This corrects the intent: it said commons already requires 3.14 for PyHX, so PyHX couldn't be installed below 3.14 anyway, and the change would be a `feat:`. That was read from a local commons checkout on 1.x; the commons PyHX actually locks (0.2.1) runs on 3.12. So today PyHX installs on 3.12 and 3.13, and raising the floor and moving to commons 1.x break apps there. The developer decided on `feat!` (R8); below 1.0.0 that bumps the minor version (0.4.0), still on PyHX's `versions/0`.

### Code

Ruff takes its target version from `requires-python`, so raising the floor (R1) is what makes the linters report the 3.14 idioms; there is no separate `target-version` setting. mypy checks against the running interpreter, which is 3.14 locally and, after R5, in CI.

Checked against the code (ruff with target `py314`, on `src/pyhx`, which is what `poe check` lints):

- `ruff check` reports 63 findings, all auto-fixable: 62 × UP037 (quoted annotations, which 3.14's deferred evaluation of annotations, PEP 649, makes unnecessary; mostly `core/primitives/path_template.py`, `components/view_model/color.py`, `components/data/annotations/column.py`, `core/request_context.py`) and 1 × UP035 (the `typing_extensions` import of R3).
- `ruff format --check` wants 4 files reformatted: `except (A, B):` becomes `except A, B:` (PEP 758) in `components/data/_table_helpers.py`, `components/data/data_section.py`, `core/primitives/negotiate_timezone.py` and `core/static.py`.
- `mypy --python-version 3.14` reports no issues.

So the code part is `poe fix` (or `ruff check --fix` and `ruff format`) after R1, reviewed by hand, and nothing more. The three modules with `from __future__ import annotations` keep it; ruff doesn't report them, and removing it would be a wider modernisation (R4). `typing-extensions` stays installed as a dependency of pydantic and FastAPI.

### CI

`python-check.yml` and `python-docs.yml` of core--devops-workflows default to `python-version: "3.12"` and take it as an input; commons already passes `"3.14"`. PyHX's callers get the same `with:` block. `python-release.yml` runs release-please and installs no Python, so `release.yml` stays unchanged (a deviation from the intent's "releases run on Python 3.14", which doesn't apply).

### Sample

`new_id()` returns the same 36-character string format as `str(uuid4())`, so the sample's hidden field and tests keep working. Using commons' function instead of `uuid7()` directly follows the rule to use our own libraries first.

### Migration (for R8)

Apps on PyHX:

1. Run on Python 3.14 and raise their `requires-python` to `>=3.14, <4.0`.
2. If they reference commons themselves, move it to `branch = "versions/1"` (commons' own migration: nothing else in its API changed; note its 1.1.0 ids are UUIDv7, which reveal their creation time).
3. If their CI uses the shared `python-check.yml`/`python-docs.yml`, pass `python-version: "3.14"`.

## Alternatives considered

- **Stay on commons `versions/0` and only raise PyHX's floor:** PyHX would require 3.14 while its commons doesn't, and it couldn't use `new_id()`; the reason for the floor would be missing.
- **Use `uuid.uuid7()` directly in the sample:** commons offers `new_id()` for exactly this; using it keeps ids of the sample and of commons consistent.
- **Set `target-version = "py314"` in `[tool.ruff]` instead of relying on `requires-python`:** duplicates the floor in a second place that can drift; ruff reads `requires-python` already.
- **Also lint `samples/` and `tests/` for 3.14:** they already have 113 ruff findings at the current target and aren't part of `poe check`; cleaning them is a separate change.
- **Use UUID v7 for the DOM ids in the components:** their order doesn't matter (intent), so it would be churn without benefit.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Released as `feat:`, not `feat!` | Changed by the developer to `feat!` (R8), see Design, "Why the floor moves" |
| core--devops-workflows and commons stay unchanged | R5 uses the existing `python-version` input; R2 only references the released commons 1.x |
| The public API of PyHX stays unchanged | R3 and R4 change imports, annotations and formatting only; R4's `poe check` (pytest) proves behaviour |
| 3.14 idioms only where the linters ask; `poe check` clean | R4, Design (the 63 findings and 4 files listed) |

## Open questions

None.

## Areas of concern

1. **Unquoted annotations at runtime** (R4): removing the quotes relies on PEP 649. pydantic (2.13.4) and FastAPI (0.141.1) read annotations of models and endpoints at runtime; a forward reference that was only safe as a string could fail at import or when a model is built. Covered by the full test suite in `poe check` and by starting the samples in `tests/samples`. Owner: Michael Wellner.
2. **commons 1.x in PyHX** (R2): the update may also bring newer versions of commons' dependencies (sqlmodel, sqlalchemy, pandas). The login token and user code PyHX uses is unchanged in its API, but this is proved only by the tests. Owner: Michael Wellner.
3. **First CI run on 3.14** (R5): the shared workflows use Poetry 2.5.1 and `actions/setup-python`; commons runs them on 3.14 already, so the risk is low. The PR's check is the proof. Owner: Michael Wellner.
4. **Platform standard still names 3.12:** the note `core--docs/notes/2026-10-30-1905--python-libraries-on-github.md` of core--platform (and so presumably the skill `scaffold-python-library`) says `requires-python = ">=3.12, <4.0"`, while commons and now PyHX require 3.14. Not changed here (other repository). Owner: Michael Wellner.

## Out of scope

- Changes to commons itself.
- core--devops-workflows' default `python-version`, and the platform note of concern 4.
- UUID v7 for DOM element ids in the components; they stay `uuid4`.
- Ruff findings in `samples/` and `tests/`, and further modernisation (`from __future__ import annotations`, PEP 695 generics, which stay ignored as UP046/UP047).
- `release.yml`, which runs no Python.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **F1** Moving commons from `versions/0` to `versions/1` changed exactly one locked package, commons 0.2.1 → 1.1.0; none of its dependencies moved, and no commons signature PyHX uses changed.
- **F2** CI had to move to 3.14 before the floor was raised: pushed the other way round, the check on 3.12 would have failed.
- **F3** `poe fix` reformatted 5 files, not 4: besides the 4 `except` rewrites, `components/primitives/conditional_select.py` put a signature on one line once its return annotation lost its quotes.
- **F4** The app shell sample had no tests; `tests/samples/app_shell_layout/test_data_page.py` is the first, checking that new record ids are UUID v7.

Rollout: PR #10 (`feat!: Upgrade to Python 3.14 and commons 1.x`), released with the next Release PR as PyHX 0.4.0 on `versions/0`. The check ran on CPython 3.14.9 and passed.

Open after this change: the platform note `core--docs/notes/2026-10-30-1905--python-libraries-on-github.md` of core--platform (and presumably the skill `scaffold-python-library`) still names `requires-python = ">=3.12, <4.0"`, and core--devops-workflows still defaults to Python 3.12. Owner: Michael Wellner.
