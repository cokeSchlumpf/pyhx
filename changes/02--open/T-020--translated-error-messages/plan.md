# T-020 Translated error messages: plan

## Findings while planning

- **F1** `DataForm` and `HeadlessForm` each reduce a `ValidationError` to `err["msg"]` per field in `_validation_errors_to_dict`; errors without a field are skipped.
- **F2** `pyhx.notifications.js` shows `xhr.statusText` on `htmx:responseError`, never the response's text.
- **F3** The page, fragment and API wrappers of `webapp.py` re-raise errors for which the FastAPI app has a handler; FastAPI always has one for `HTTPException`, so those already reach FastAPI's JSON handler.
- **F4** `stream._render_error` already hides the trace outside development; only its title is English.

Deviations from the spec:

- None yet.

## Branching

Branch `feature/translated-error-messages`, worked on in its own worktree (the main checkout is on T-019); one PR, squash-merged after its checks, then the Release PR. The steps run without review stops, as part of an app change that runs without them.

## Steps

### 1. Validation messages

- `validation_message`, used by both forms. **R1, R2, R3**
- Proof: tests in `tests/pyhx/i18n/test_validation.py` (en, de; limits; prefix; custom messages) and a German form test.

### 2. Toasts, error pages, fragment, endpoint and stream errors, HTTP errors

- **R4–R10**
- Proof: tests in `tests/pyhx/core/test_errors.py`; existing stream and auth addon tests.

### 3. Catalogs and docs

- **R11, R12**
- Proof: `poe check` green.

## Risks

- **Catalog conflicts with T-019:** rerun `pyhx.i18n update` after merging main.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1–R3 | Step 1 tests |
| R4, R5 | Step 2, test of the template's texts; JS reviewed in a browser |
| R6–R10 | Step 2 tests |
| R11, R12 | Step 3, `poe check` |
