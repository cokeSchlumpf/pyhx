# T-008 Quick filters and search for data tables: plan

## Findings while planning

- **F1** There are no tests for `url_param_keys` (neither drawer headers nor `pyhx.filter-drawer.js`) and none for `sql_query.py`; the steps add tests for both paths they touch (SQL against an in-memory SQLite with SQLAlchemy 2.0.52, which has `icontains(autoescape=True)`).
- **F2** htmx is 2.0.4: `hx-include` takes comma-separated extended selectors (`find input:checked`), and `hx-preserve` is honoured in out-of-band swaps, which the table uses (`hx-swap-oob="outerHTML"` on the wrapper).
- **F3** `Option.label` of the segment control is a plain `str`, so a count is part of the label text ("Alle 8"), as in the draft.
- **F4** The sample's `status` is a `str` enum in a `TextColumn`; its derived filter is a single-select choice (only "equals" in the drawer), so a preset with two statuses ("Offen") wouldn't show in the drawer. The sample marks the column with `MultipleChoiceFilter` so presets use `TextChoiceIn`.
- **F5** `str(enum_member)` of a `str` enum is `"CaseStatus.new"`, not its value; the search reads `Enum.value` (spec R3 already says so).
- **F6** The cherry-picked commit 8f68de9 (DataPage sample) carries a `Co-Authored-By` trailer from its own stream; it is kept as picked.
- **F7** The apps (beleglotse, cross-border-rules) implement `do_fetch` only and use their own query parameters (`status`, `match`, …) on other pages; the bootstrap reads only parameters a table is configured for, so they are unaffected.

Deviations from the spec:

- none so far.

## Branching

Branch `feature/quick-filters` from `origin/main` (ec8696b), one pull request at the end. On the developer's instruction the steps are implemented without pausing for reviews; each step is committed and pushed, and the review happens at the pull request.

## Steps

### 1. Search and counts in the query and the sources

- `Query.search` / `search_keys`, `clear`, `is_active_filter_or_sort`, `extract`; search in `apply_query` / `count_matches`; search in `apply_sql_filters`; `supports_search` and `count` on `ReadOnlyDataSource`, `SimpleDataSource`, the mapped and the `App…` sources. **R1, R2, R3, R4, R5, R6**
- Proof: unit tests for in-memory search (case, enum, `None`, AND with conditions under `filter_mode="any"`), `count_matches`, `extract`, SQL search on SQLite (escaping `%`), counts and capabilities of each source; the existing source tests stay green.

### 2. Searchable columns and the quick filter model

- `Column.searchable`, `TextColumn(searchable=…)` through the reader; `quick_filter.py` with `QuickFilter`, `QuickFilters`, `TableSearch`, `apply_quick_filter`, `active_quick_filter`, validation. **R7, R9, R10**
- Proof: unit tests for the reader flag, apply (other columns, sort, search kept), active and "custom" (Q3), validation errors.

### 3. Quick filter bar, search field and URL in `DataTable`

- `DataTable(quick_filters=, search=)`: bar with pills (segment control) and search field, `render_table` actions, counts, `search_keys` from columns, `hx-preserve` on search responses, URL data attributes and the listener in `pyhx.table.js`, bootstrap from the URL, `DataTable.query()`, `url_param_keys` written by the table; drawer shows and keeps the search. Styles in `table.css`. **R8, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R23**
- Proof: render tests (radio group with label and checked pill, none checked for custom, counts on/off with a counting probe, search field shown only with a searchable column and a supporting source), fragment tests through a `TestClient` (pill click, search, drawer apply keeps search, clear), URL attribute values, bootstrap from query parameters; browser check of typing, focus and address bar in step 5.

### 4. DataSection and DataPage

- `table_quick_filters`, `table_search`, `table_url_param_keys`, `TypeError` for a hierarchical source, "Filter & Sort" button from `DataTable.query()`. **R21, R22**
- Proof: tests that the options reach the table (bar rendered by a `DataPage`, deep link filtered), the `TypeError`, and the highlighted button on a filtered first paint.

### 5. Samples, screenshots, guide

- Canvas DataPage with quick filters (counts), search and the dossier link; app shell DataPage with quick filters and search; `docs/guides/data-tables.md` and `mkdocs.yml`. **R23, R24, R25**
- Proof: sample tests (bar rendered, deep link filtered, dossier link), the Playwright script (before/after, active pill, search, drawer, deep link, custom, 390px, app shell; URL updated and kept after reload), `poe docs-build`-equivalent `mkdocs build --strict`, full test suite, ruff, mypy.

## Risks

- **Focus and typed characters in the search field:** checked in the browser with the screenshot script (type, wait, type more, compare value and `document.activeElement`).
- **URL sync on swaps that don't concern the table:** the listener writes the same values again (idempotent); checked by the script after opening the drawer.
- **Pills look in the default design:** checked in the app shell screenshot.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1, in-memory and SQL search tests |
| R2 | Step 1, `Query` tests |
| R3 | Step 1, in-memory tests (enum, `None`, case) |
| R4 | Step 1, SQLite tests |
| R5 | Step 1, source capability and count tests |
| R6 | Step 1 and 3, existing tests unchanged and green |
| R7 | Step 2, reader test |
| R8 | Step 3, render test |
| R9 | Step 2 unit tests, step 3 pill-click fragment test |
| R10 | Step 2 unit tests, step 3 render test (custom), step 5 screenshot |
| R11 | Step 3 render test |
| R12 | Step 3 counting probe tests |
| R13 | Step 3 render tests |
| R14 | Step 3 (`hx-preserve` on search response), step 5 browser check |
| R15 | Step 3 test with tampered `search_keys` |
| R16 | Step 3 drawer tests, step 5 screenshot |
| R17 | Step 3 attribute tests, step 5 browser check of the address bar |
| R18 | Step 3 bootstrap tests, step 4 deep link test, step 5 reload check |
| R19 | Step 3 test |
| R20 | Step 3 test with `url_param=None` |
| R21 | Step 4 tests |
| R22 | Step 4 test |
| R23 | Step 5 screenshots (canvas, 390px, app shell) |
| R24 | Step 5 sample tests and screenshots |
| R25 | Step 5 guide, strict docs build |
