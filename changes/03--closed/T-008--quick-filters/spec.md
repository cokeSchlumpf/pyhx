# T-008 Quick filters and search for data tables: spec

## Requirements

### Query and data sources

- **R1** `Query` carries a search term (`search`, `None` when there is none) and the keys it is searched in (`search_keys`). An item matches the search when the value of at least one of the `search_keys` contains the term, ignoring case; the search combines with the filter conditions by AND, whatever `filter_mode` is.
- **R2** `Query.clear()` also removes the search term, and `Query.is_active_filter_or_sort()` is `True` while a search term is set. `Query.extract()` keeps the search on the remaining query.
- **R3** The in-memory evaluation (`apply_query`, `count_matches`, so `SimpleDataSource` and `SimpleHierarchicalDataSource`) applies the search as in R1; an enum value is searched by its value, `None` never matches.
- **R4** `apply_sql_filters` (so `apply_sql_query`) applies the search as a case-insensitive `LIKE` over the mapped `search_keys`, with `%` and `_` in the term matched literally; keys without a mapped column are skipped.
- **R5** Every `ReadOnlyDataSource` has `supports_search` (default `False`) and `async count(query) -> int | None` (default `None`, meaning "no number"). `SimpleDataSource` supports search and counts in memory; `MappedReadOnlyDataSource` passes both on to its inner source; the `App…DataSource` classes offer `do_count` (base classes) and `count=` / `supports_search=` (function variants).
- **R6** Existing data sources and apps that implement only `fetch` keep working unchanged: no abstract method is added, and a table without quick filters and searchable columns renders and behaves as before.

### Columns

- **R7** A column can be marked searchable: `Column(searchable=True)` and `TextColumn(searchable=True)`; the default is `False`.

### Quick filters

- **R8** `DataTable` takes `quick_filters=QuickFilters(presets=[QuickFilter(key, label, filter), …])` and renders the presets as pills in a bar above the table header, in the given order; the app passes "all" as a preset without conditions, first.
- **R9** Choosing a pill replaces the table's conditions on the columns any preset filters (the preset columns) with the chosen preset's conditions; sort, search and conditions on other columns stay.
- **R10** A pill is shown as active when the table's conditions on the preset columns are exactly the preset's; when they match no preset (e.g. after the drawer changed the status condition) no pill is active ("custom"). A drawer condition on another column leaves the active pill active.
- **R11** The pills are a labelled group (`aria-label`, default "Quick filters") of radio buttons with the active one checked, reachable and operable by keyboard.
- **R12** With `QuickFilters(counts=True)` each pill shows the number of items the table would show after choosing it (`source.count` of the current query with the preset applied); a pill whose count is `None` shows no number. With `counts=False` (default) `count` is not called.

### Search

- **R13** The table shows a labelled search field in the bar when at least one of its columns is searchable and its source supports search; label, placeholder and URL parameter come from `search=TableSearch(…)` (defaults: "Search", none, `q`).
- **R14** Typing in the field filters the table after a short pause (and on Enter / clearing the field); characters typed while a request runs are kept, and the field keeps the focus.
- **R15** The table fills `search_keys` from its searchable columns on every render, so a stale or tampered state can't search other fields.

### Filter drawer

- **R16** The filter drawer opened on a table shows the combined query: the conditions a pill set (as normal conditions) and the search term; Apply keeps the search term, Clear removes it with the rest.

### URL

- **R17** After every change of the table's query (pill, search, drawer Apply/Clear, toolbar clear, header sort click) the address bar holds the active pill's key (`?view=<key>`, omitted for a preset without conditions and for "custom"), the search term (`?q=<term>`) and the `url_param_keys` conditions, without a page reload or history entry; other URL parameters stay.
- **R18** A table rendered on a page request without table state starts from the URL: the preset named by the quick filter parameter, then the `url_param_keys` (a single-value condition: `TextChoiceIn` for a multi-select choice column, otherwise `TextChoiceEquals`), then the search term. Unknown preset keys are ignored. Reloading the page keeps the filter; another page can link to a filtered list.
- **R19** `url_param_keys` conditions written to the URL are `TextChoiceEquals` or a `TextChoiceIn` with exactly one value; other conditions on such a key remove the parameter (as today).
- **R20** The quick filter and search URL parameters are configurable (`QuickFilters(url_param=…)`, `TableSearch(url_param=…)`) and can be switched off with `None`.

### DataSection and DataPage

- **R21** `DataSection` and `DataPage` take `table_quick_filters`, `table_search` and `table_url_param_keys` and pass them to their table; `table_url_param_keys` also reaches a hierarchical table, quick filters and search on a hierarchical source raise a `TypeError`.
- **R22** The page-header "Filter & Sort" button of a `DataSection` starts highlighted when the table starts filtered from the URL.

### Styles, samples, documentation

- **R23** The bar matches the design draft in the canvas design (pills 22px high, 12px/500, active filled dark with white text, others light grey; search right, label "Suchen" in the sample, 32px field, 260px) and fits the default design through the same tokens; at phone width (390px) pills and search wrap without horizontal scrolling.
- **R24** `samples/canvas_layout` shows quick filters with counts and search on its DataPage (status Alle / Offen / Eingabe erforderlich / Abgeschlossen; search over Fallnummer, Name, AHV-Nr.) and links from the dossier's "Handlungsbedarf" to the cases that require input; `samples/app_shell_layout` shows them on its DataPage in the default design.
- **R25** The data table guide documents quick filters, counts, search, the URL parameters and what a custom data source implements for search and counts.

## Design

### Query and search semantics

`Query` gets two fields:

```python
search: str | None = None
search_keys: list[str] = Field(default_factory=list)
```

The term lives in the query (constraint: the query is the single source of truth); the keys live there too, so a source can apply the search without knowing the table's columns. The table owns the keys (R15): `_render_from_state` sets `query.search_keys` from the resolved searchable columns before `fetch` and `count`. Search is AND-combined with the conditions regardless of `filter_mode`: it is an independent narrowing, not one more condition among the "any" ones.

Clarification of Q2 (the developer asked "that is like it is today?"): it is not. Today a query can only hold per-column conditions (`StringContains` etc. in `sources/filter.py`) combined by one global `filter_mode`; "a term in any of several columns AND the other conditions" can't be expressed (with `filter_mode="any"` the other conditions would become OR, too). So search is new. It is "contains" like `StringContains`, but ignoring case (the in-memory `StringContains` is case-sensitive, a search field shouldn't be).

In memory (`_query.py`): `_matches_query` checks the conditions as before, then `_matches_search(item, query)`: no term or no keys → `True`; else `any(term.casefold() in _search_text(value_of(item, k)).casefold())`, where `_search_text` takes `Enum.value`, `str()` of other values and `None` → no match. `count_matches` takes the shortcut only when there is neither a filter nor a search.

SQL (`sql_query.py`): `apply_sql_filters` adds `or_(*(columns[k].icontains(term, autoescape=True) for k in search_keys if k in columns))` with `and_`. `extract` copies `search`/`search_keys` to `remaining` only: search is one OR across its keys and can't be split.

### Source capabilities

```python
class ReadOnlyDataSource[T](ABC):
    supports_search: bool = False
    async def count(self, query: Query) -> int | None:
        return None
```

Concrete, so no subclass breaks (R6). `SimpleDataSource`: `supports_search = True`, `count` = `count_matches(self._data, query)`. `MappedReadOnlyDataSource`: `supports_search` is a property returning the inner source's; `count` maps the query (`map_query`) and delegates. `AppReadOnlyDataSourceBase`: `count` dispatches to a new `do_count(registry, user, query)` returning `None` by default; an app opts into search with `supports_search = True` on its subclass (and applies `query.search`, e.g. via `apply_sql_query`). `AppReadOnlyDataSource` / `AppDataSource` take optional `count=` (sync or async function like the others) and `supports_search=False`. Hierarchical sources are not changed (quick filters are for flat tables).

### Quick filter model (`components/data/quick_filter.py`)

```python
@dataclass(frozen=True, kw_only=True)
class QuickFilter:
    key: str                      # URL value, unique
    label: str
    filter: Sequence[Condition] = ()   # at most one condition per column

@dataclass(frozen=True, kw_only=True)
class QuickFilters:
    presets: Sequence[QuickFilter]
    counts: bool = False
    label: str = "Quick filters"   # aria-label of the group
    url_param: str | None = "view"

@dataclass(frozen=True, kw_only=True)
class TableSearch:
    label: str = "Search"
    placeholder: str | None = None
    url_param: str | None = "q"
```

`QuickFilters.__post_init__` rejects duplicate preset keys and a preset with two conditions on one column. Two pure functions do the logic:

- `apply_quick_filter(query, preset, quick_filters) -> Query`: a deep copy without the conditions on the preset columns (union of the presets' condition keys), plus the preset's conditions.
- `active_quick_filter(query, quick_filters) -> QuickFilter | None`: the first preset whose conditions equal the query's conditions on the preset columns (compared by key and `model_dump()`).

That is the whole Q3 behaviour: the drawer edits the same conditions; on another column they don't take part in the comparison, on a preset column a changed condition matches no preset (or exactly another one, which is then active).

### Table rendering

`DataTable(quick_filters=None, search=None)` (both keyword-only, additive). `_render_from_state` renders, inside the table primitive's `controls` before the icon toolbar, a bar `div.hx-table__filter-bar` when there are presets or a search field:

- Pills: `segment_control("quick_filter", options, value=active_key, aria_label=…, class_="hx-table__quick-filters")` — the existing radio group, restyled as pills in the bar (one radio checked or none; arrow keys move and choose like tabs with automatic activation). The group posts on `change` to the table's `render-table` fragment with `action=quick_filter` (`hx-include` = the table state plus `find input:checked`). Labels with counts are `"Alle 8"` as in the draft.
- Search: `label.hx-table__search > span + input[type=search]` with a stable id, `name="search"`, posting `action=search` on `input changed delay:300ms, search`. In the response to a search request the input carries `hx-preserve`, so htmx keeps the element the user is typing in (value, focus, caret) instead of the server's copy (R14); in every other response it is replaced, so Clear and a URL bootstrap show the right value.

`render_table` handles the two new actions by `apply_quick_filter` (unknown keys ignored) and by setting `state.query.search` (stripped, empty → `None`).

Counts (R12): only when `counts=True`, one `await source.count(apply_quick_filter(query, p))` per preset.

### URL sync and bootstrap

The table, not its drawer, now owns the URL: it no longer forwards `url_param_keys` to its internal `FilterDrawer` (a standalone `FilterDrawer` keeps its header mechanism unchanged). Every render puts `data-hx-url-param-keys="view,q,status"` and `data-hx-url-params="view=open&q=meier"` on the table wrapper; a listener in `pyhx.table.js` mirrors them into the address bar with `history.replaceState` after each htmx swap (`htmx:afterSwap`, `htmx:oobAfterSwap`), removing tracked keys without value and leaving all other parameters. This covers every way the query changes (R17), including drawer Apply, which re-renders the table out of band.

`DataTable._read_state` without table state in the request builds the initial query from `request.query_params` (R18), only for the parameters configured (a table without quick filters ignores `?view=`). `DataTable.query()` (new, public) returns the query the table renders for the current request; `DataSection.render_actions` uses it for the "Filter & Sort" button (R22).

### Filter drawer

`FilterDrawerValue` already is-a `Query`, so `search` bootstraps from the table state. The filter view shows the term as a read-only line ("Search: “meier”") with a hidden `search` input so drawer requests keep it; `FilterDrawerValue.clear()` removes it (R16). `search_keys` is not round-tripped (R15).

### DataSection / DataPage

New keyword parameters `table_quick_filters: QuickFilters | None`, `table_search: TableSearch | None`, `table_url_param_keys: list[str] | None`, forwarded `DataPage` → `DataSection` → `DataTable` (`table_url_param_keys` also to `HierarchicalDataTable`).

### Styles

In `primitives/table.css` (pyhx layer, tokens only): the bar is a wrapping flex row (`justify-content: space-between`, padding 12px 16px, bottom border); pills restyle `.hx-table__quick-filters .hx-segment-control__option` (height 22px, radius full, `--hx-color-neutral-100` / `-700`, checked `--hx-color-neutral-900` / `--hx-color-background`, 12px/500), the search label 13px `--hx-color-neutral-700`, the input 260px × 32px. The canvas theme's token values give the draft's colours (#F3F3F3, #404040, #171717); no canvas-specific rule is needed. Below 600px the search takes the full width under the pills. The table card look itself (T-006) is not touched.

### Samples, docs

As R24 / R25. There is no data table guide in `docs/` yet; this change adds `docs/guides/data-tables.md` (quick filters, counts, search, URL, custom sources) and links it in `mkdocs.yml`.

## Alternatives considered

- **Search as a `StringContains` condition per column with `filter_mode="any"`:** can't be combined with other conditions by AND (one global mode), and mixes the search into the drawer's conditions.
- **Search keys configured on the source instead of in the query:** every source would need the table's column knowledge; with keys in the query `SimpleDataSource` and `apply_sql_query` work without configuration.
- **Pill state as a separate field in `TableState`:** a second source of truth beside the query; the drawer couldn't show it and Q3 ("custom") would need extra syncing. Deriving the active pill from the conditions keeps the query the only truth.
- **Only `url_param_keys` for deep links (no `?view=`):** works only for presets that are a single `TextChoiceEquals`; "Offen" (two statuses) couldn't be linked.
- **Keeping the URL headers in the drawer and adding them to every table fragment:** the headers would have to be built in four places (drawer, render, sort, clear); the data attributes on the re-rendered wrapper cover all of them in one place.
- **Toggle buttons with `aria-pressed` for the pills:** would need new markup and JS for keyboard handling; the segment control is an existing, accessible radio group (one of two, exactly the "one active at a time" semantics).
- **Abstract `count` / `supports_search` on the source:** would break every app source.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| The table's `Query` stays the single source of truth; presets and search are expressed in it | R1, R9, R10, R15, design "Quick filter model" |
| Existing data sources and apps keep working unchanged; search and counts opt-in | R5, R6, R7 (default off), R13 |
| No count query per pill when counts are off | R12 |
| Pills are a labelled group of toggle buttons (or a segment control), the search field has a label | R11, R13 |

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal.

### Q1 How are counts computed? (from the intent)

**Proposal:** Optional per table (`counts` off by default). When on, the source is asked for a count per preset; `SimpleDataSource` counts in memory, other sources implement a count method or show no number.

**Answer:** Yep. (accepted in the intent; a pill's number is what the table would show after choosing it, i.e. combined with the search and the other conditions)

### Q2 How does search reach the source? (from the intent)

**Proposal:** `Query` gets a search term and the columns get a `searchable` flag; a source applies the term as "contains, ignoring case" over those columns. Sources that don't support search hide the field.

**Answer:** "Yes, that is like it is today?" Clarification: it is not like today; today only per-column conditions with one global all/any mode exist, which can't express "term in any of these columns AND the other filters". Accepted as proposed (decided by the agent on the developer's instruction to implement without stopping), see Design "Query and search semantics".

### Q3 Pill and drawer filter on the same column (from the intent)

**Proposal:** A preset sets its conditions; a drawer condition on another column is kept, one on the same column replaces the preset's and the pill shows as "custom" (no pill active).

**Answer:** Yep.

### Decisions taken without stopping

The developer asked for the change to be implemented without stops; these decisions were taken by the agent and are listed for review at the pull request:

- API names: `QuickFilter`, `QuickFilters`, `TableSearch`, `Query.search` / `search_keys`, `ReadOnlyDataSource.supports_search` / `count`, `Column.searchable`, `TextColumn(searchable=…)`, `DataTable(quick_filters=, search=)`, `DataSection` / `DataPage(table_quick_filters=, table_search=, table_url_param_keys=)`, `DataTable.query()`.
- URL parameters `view` (pill) and `q` (search) by default, configurable, `None` switches off.
- "All" is not built in; the app passes it as the first preset without conditions (keeps labels in the app until i18n lands).
- Search is AND-combined with the conditions regardless of `filter_mode`, and ignores case (unlike `StringContains`).
- The table writes `url_param_keys` to the URL itself (data attributes + `pyhx.table.js`) instead of forwarding them to its drawer.
- A new guide `docs/guides/data-tables.md`, as there is no data table guide yet.

## Areas of concern

1. **Two tables with quick filters on one page** (R17, R20): both would write `?view=`. The defaults fit a page with one list (DataPage); a page with several sets different `url_param`s or `None`. Documented in the guide. Owner: app developer.
2. **App sources that set `supports_search = True` but don't apply `query.search`** (R5): the field would filter nothing. Documented; `apply_sql_query` does it for SQL sources. Owner: app developer.
3. **Typing while a search request runs** (R14): relies on htmx 2's `hx-preserve` in out-of-band swaps; verified in the browser (screenshot script). Owner: agent.
4. **Counts cost** (R12): one `count` per preset per render; off by default, and in-memory counting is linear. Owner: app developer (turn on only with a cheap `count`).
5. **`filter_mode="any"` and presets** (R9): a preset's conditions are OR-combined with drawer conditions on other columns when the user switches the drawer to "any"; the drawer shows exactly that. Accepted, not special-cased. Owner: agent.
6. **Search on non-text columns in SQL** (R4): `icontains` on a non-string column depends on the database; searchable is meant for text columns (documented). Owner: app developer.

## Out of scope

- Views saved by users, full-text search in a database, filter chips for the drawer's conditions (as in the intent).
- Quick filters and search on `HierarchicalDataTable` (and `count` on hierarchical sources); `url_param_keys` bootstrap there.
- The canvas look of the page header and table card (T-006).
- Translating the built-in defaults ("Quick filters", "Search", the drawer's labels); that is the i18n stream.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** `segment_control` got an optional `input_id_prefix` (ids on the radios), so htmx gives the focus back to the chosen pill after the table re-renders; not named in the spec.
- **D2** After merging `main` (i18n, #20) the built-in defaults are translated: `QuickFilters.label` ("Quick filters") and `TableSearch.label` ("Search") are `Text` (`_l(...)`), with de/it/fr catalog entries; `QuickFilter.label` and `TableSearch.placeholder` accept `Text` too. The drawer's "Search" heading is translated as well.
- **D3** The table reads the URL on first paint only for the parameters it uses (search only when the search field is shown), so pages with their own `?q=` or `?view=` are not affected.
- **D4** The filter bar sits above the table's bordered scroll container, lined up with the cells' text; the draft's card around bar and table is the table card look of T-006.
- **F1** htmx 2.0.4 keeps an `hx-preserve` element in out-of-band swaps, so the search field keeps typed characters, focus and caret while requests run (checked in the browser: "mei" + "er" typed across a request gives "meier", focus kept).
- **F2** `str()` of a `str` enum is `"Status.new"`, so the search reads `Enum.value`.
- **F3** Pre-existing, not part of this change: in the canvas DataPage the sticky page header and table header paint over the open drawer (fixed by T-006, #29), and the canvas page header breaks at phone width (T-006). The app shell sidebar lost its layout in German on `main` at the time; #34 fixed it, and the app shell screenshots are taken in German.
- **F4** `main` needs `commons` 1.4.0; the shared virtualenv had 1.2.0, so checks ran with commons 1.4.0 on `PYTHONPATH`.

- **F5** The screenshots are kept in `screenshots/` next to this spec (locale de-CH): canvas DataPage [before](screenshots/canvas-shell--data-page--before.png) and [after](screenshots/canvas-shell--data-page--after.png), a [pill chosen](screenshots/canvas-shell--data-page--pill-active.png), a [search](screenshots/canvas-shell--data-page--search.png), the [drawer with the combined query](screenshots/canvas-shell--data-page--drawer.png), the [deep link from the dossier](screenshots/canvas-shell--data-page--deep-link.png), the ["custom" state](screenshots/canvas-shell--data-page--custom.png), [phone width](screenshots/canvas-shell--data-page--phone.png); app shell DataPage [after](screenshots/app-shell--data-page--after.png) and with a [pill chosen](screenshots/app-shell--data-page--pill-active.png).

Rollout: pull request #30 from `feature/quick-filters`, released with the next minor version of pyhx. The apps adopt it by passing `table_quick_filters` / `table_search` and marking columns searchable; nothing changes for them otherwise.

Open after this change: quick filters and search on `HierarchicalDataTable` (if needed, app developers); `count` and search in the apps' SQL sources (case-sight first); the canvas page header at phone width (F3, T-006).
