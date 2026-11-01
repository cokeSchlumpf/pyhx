# T-004 Multilingual apps: plan

## Findings while planning

- **F1** pyhx has no built-in routes; the auth addon registers its routes and owns the session (`configure_user_session`) and the users repository (`CookieUserSession`).
- **F2** `RequestContext` is built per request (`build_from_request`) with `request.state.user` loaded by `CookieUserSession`; `login_user`/`logout_user` touch only their own session keys.
- **F3** `negotiate_locale()` is called per cell by the readers in `components/data/annotations/reader.py`; `humanize` is used only there (`naturaltime`).
- **F4** Babel 2.18 checkers cover only `%` formats; `.mo` files are ignored by `.gitignore`.
- **F5** `poe check` lints only `src/pyhx`; `pytest` runs `tests/` including `tests/samples`; there are no tests of `samples/user_auth` yet.
- **F6** pyhx locks commons by commit; until commons 1.4.0 is released, step 4 uses the local commons checkout in the working tree only (never committed).

Deviations from the spec:

- None.

## Branching

Branch `feature/i18n`, draft PR `feat: make apps multilingual (T-004)`. Executed by the agent as part of T-003 of `app--casesight` without review pauses per step; the PR is published only after commons 1.4.0 is released and locked; the agent presents the sample running locally, the developer reviews and merges the PR, the agent then merges the Release PR (1.3.0).

## Steps

### 1. Resolving the language

- `pyhx.i18n` with `resolve_locale`, `use_locale`, cached `RequestContext.locale`, weighted `Accept-Language`; `negotiate_locale()` delegates; `<html lang>`. **R1, R2, R3, R4, R5**
- Proof: tests of the order, weights, regional variants, skipped values, one resolution per request, `use_locale`, concurrent requests, data table in the session language, `lang` in the page.

### 2. Translating texts

- Catalog loading and cache, `locale_dir`, project-root default; `_`, `_n`, `_p`, `_l`, `t`. **R9, R10, R11**
- Proof: tests with temporary catalogs: app beats pyhx beats source, missing catalog or entry, reordered placeholders, `t` with nodes and escaping, lazy translation, plurals in de and fr.

### 3. Format helpers and relative time

- The seven helpers, readers use them, Babel relative time, `humanize` removed. **R14, R15**
- Proof: helper tests in en and de with timezone; reader tests; `pinned_locale` wins.

### 4. Switching and the login mail language

- `POST /_pyhx/locale` in `configure_user_session`, `c.locale_switcher()`, `locale` passed to `request_login`; commons 1.4.0. **R6, R7, R8, R20**
- Proof: tests for anonymous and signed-in switching, `HX-Refresh`, foreign `next`, unknown language, sign-in/out keeping the session language, login message language.

### 5. Labels, own texts, catalogs and the check

- `*Labels` and `CalendarLabels`; all user-facing literals marked; `update`/`check` command; de, it, fr catalogs (LLM); `poe check` runs the check. **R12, R13, R16**
- Proof: label round-trip test across languages; calendar names; `check` failure cases and pass on pyhx; catalog loaded from the installed package path; review of remaining literals.

### 6. Sample, docs, CLAUDE.md

- `samples/user_auth` extended, `tests/samples/user_auth/`; guide and nav; `user-authentication.md`; `LocaleSettings` docstring; rule in `CLAUDE.md`. **R17, R18, R19**
- Proof: sample tests; `poe docs-build` (strict); the sample run locally and clicked through, then presented to the developer.

## Risks

- **commons release pending:** step 4 developed against the local checkout; `poetry update commons` and a full `poe check` before the PR is published.
- **Behavior changes:** listed in the PR description.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1–R5 | Step 1 |
| R6–R8 | Step 4 |
| R9–R11 | Step 2 |
| R12, R13 | Step 5 |
| R14, R15 | Step 3 |
| R16 | Step 5 |
| R17, R18, R19 | Step 6 |
| R20 | Step 4 |
