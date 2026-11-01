# T-008 Quick filters and search for data tables

## Problem

Lists in apps have a few views users switch between all the time: in case-sight "all", "open", "requires input"; elsewhere "drafts", "mine", "overdue". With pyhx a user gets there only through the filter drawer (open it, choose a column, a condition, a value, apply), and there is no search field across columns. What exists doesn't add up to a quick filter:

- `DataTable(url_param_keys=[...])` writes a filter into the URL after Apply, but a table always starts with an empty `Query()` (`DataTable._read_state`), so a link like `/cases?status=requires_input` shows the unfiltered list.
- `DataPage` and `DataSection` don't pass `url_param_keys` on.
- There are no predefined filters (presets) and no counts per view.

The workaround is a parameterized path per view (`/cases/view/{view}`) and a data source that filters by it, which every app would have to build by hand, outside the table's query, sort and filter.

The target look is drafted on the design canvas "DataPage im CanvasShell" (https://claude.ai/artifact/5FmCxN9D8dG5cQVoLxqeE6, list): pills with counts above the table and a search field next to them.

## Proposed outcome

- A `DataTable`, `DataSection` and `DataPage` take quick filters: named presets (label and filter conditions) shown as pills above the table, one active at a time, "all" first.
- A pill can show the number of items it matches.
- A search field above the table filters across the columns the app marks as searchable.
- Quick filter, search and the filter drawer work together on the same query: the drawer shows what the pill and the search set, and sorting and column filters stay when a pill changes.
- The active pill and the search term are in the URL, and a table opened with them in the URL starts filtered, so other pages can link to a filtered list (e.g. from "Handlungsbedarf" on a dossier to the cases that require input). `DataPage` and `DataSection` pass `url_param_keys` on.
- `SimpleDataSource` supports search and counts; other sources keep working without them.
- `samples/canvas_layout` shows it on its DataPage, in both designs a sample shows it.
- Not part of this change: views saved by users, full-text search in a database, filter chips for the drawer's conditions.

## Affected users and systems

- **PyHX (library):** `DataTable`, `DataSection`, `DataPage`, `Query` and the data sources (search, counts), the filter drawer (shows the combined query), styles in both designs.
- **Samples and tests:** `samples/canvas_layout`, `samples/components` (data table), tests of the components.
- **Documentation:** the data table guide.
- **Apps:** case-sight first (case list); beleglotse and cross-border-rules can adopt it, nothing changes for them otherwise.

## Constraints

- The table's `Query` stays the single source of truth for filtering; presets and search are expressed in it, not beside it.
- Existing data sources and apps keep working unchanged; search and counts are opt-in for a source.
- Counts must not make a list noticeably slower: no count query per pill when counts are off.
- Accessibility: the pills are a labelled group of toggle buttons (or a segment control), the search field has a label.

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal.

### Q1 How are counts computed?

**Proposal:** Optional per table (`counts` off by default). When on, the source is asked for a count per preset; `SimpleDataSource` counts in memory, other sources implement a count method or show no number.

**Answer:** Yep.

### Q2 How does search reach the source?

**Proposal:** `Query` gets a search term and the columns get a `searchable` flag; a source applies the term as "contains, ignoring case" over those columns. Sources that don't support search hide the field.

**Answer:** Yes, that is like it is today?

### Q3 Pill and drawer filter on the same column

**Proposal:** A preset sets its conditions; a drawer condition on another column is kept, one on the same column replaces the preset's and the pill shows as "custom" (no pill active).

**Answer:** Yep.
