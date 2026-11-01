# Data Tables

A `DataTable` shows the items of a data source with sorting, a filter drawer and row selection; `DataSection` adds a create/edit drawer, `DataPage` makes a full page of it. This guide covers the parts that make a list quick to work with: quick filters, counts, search and links to a filtered list.

Everything below is expressed in the table's `Query` (sort, filter conditions, search term). The quick filters, the search field and the filter drawer all edit that one query, so they always agree.

## Quick filters

Quick filters are named presets of filter conditions, shown as pills above the table. Pass them to the table, or with the `table_` prefix to a `DataSection` or `DataPage`:

```python
import pyhx.components as c
from pyhx.components.data.sources.filter import Condition, TextChoiceIn


def status(*values: str) -> list[Condition]:
    return [Condition(key="status", values=[TextChoiceIn(values=list(values))])]


cases = c.DataPage(
    routes=router,
    path="/cases",
    source=cases_source,
    type=Case,
    table_quick_filters=c.QuickFilters(
        presets=[
            c.QuickFilter(key="all", label="All"),
            c.QuickFilter(key="open", label="Open", filter=status("new", "in_progress")),
            c.QuickFilter(key="requires-input", label="Requires input", filter=status("requires_input")),
        ],
        counts=True,
    ),
)
```

- Pass "all" yourself, first, as a preset without conditions; it is active on an unfiltered table.
- Choosing a pill replaces the conditions on the preset columns (every column a preset filters) with the pill's; sorting, the search term and conditions on other columns stay.
- The active pill is derived from the query: a pill is active when the conditions on the preset columns are exactly its own. When the filter drawer changes the status condition to something no preset has, no pill is active ("custom"); a drawer condition on another column keeps the pill active.
- A preset has at most one condition per column. For a column the drawer should show as "is any of", give the column a multi-select filter (`a.TextColumn(filter=a.MultipleChoiceFilter(options=…))`) and use `TextChoiceIn` in the presets.
- The pills are a labelled radio group (`QuickFilters(label=…)`, default "Quick filters", translated), operable with the arrow keys.

### Counts

With `counts=True` each pill shows how many items the table would show after choosing it, combined with the current search and the other conditions. The table asks the source with `await source.count(query)` once per pill and render; a source that returns `None` (the default) shows no number. Counts are off by default; turn them on only for sources that count cheaply.

## Search

Mark the columns the search looks in as searchable:

```python
class Case(BaseModel):
    case_number: Annotated[str, a.TextColumn(label="Case", searchable=True)]
    client_name: Annotated[str, a.TextColumn(label="Client", searchable=True)]
```

The table then shows a search field above the header, if its source supports search. Label, placeholder and URL parameter come from `TableSearch`:

```python
table_search=c.TableSearch(label="Search", placeholder="Case, client")
```

An item matches when one of the searchable columns contains the term, ignoring case; the search narrows the result of the filter conditions (AND), also when the drawer is set to "match any filter". The filter drawer shows the term; its Clear removes it, as does the table's own clear button.

## Links to a filtered list

The active pill and the search term are kept in the address bar (`?view=open&q=meier`) without reloading the page, and a page opened with them starts filtered. Another page can link to a filtered list:

```python
c.button("Cases requiring input", href="/cases?view=requires-input")
```

- The parameter names are `view` and `q`; change them with `QuickFilters(url_param=…)` and `TableSearch(url_param=…)`, or keep a feature out of the URL with `None`. Give two tables on one page different names.
- `table_url_param_keys=["status"]` (`url_param_keys` on `DataTable`) also mirrors single-valued conditions of these columns, e.g. `?status=closed`: a `TextChoiceIn` for a multi-select choice column, a `TextChoiceEquals` otherwise.
- The page-header "Filter & Sort" button of a `DataSection` is highlighted when the table starts filtered from the URL.

## Search and counts in your own data source

`SimpleDataSource` searches and counts in memory. Other sources opt in:

- **Search:** set `supports_search = True` and apply `query.search` over `query.search_keys` in `fetch` (and `count`). The table fills `search_keys` from its searchable columns. With SQLAlchemy, `apply_sql_query` (or `apply_sql_filters`) does it: a case-insensitive `LIKE` over the mapped columns, with `%` and `_` in the term matched literally. Search is meant for text columns.
- **Counts:** override `async count(query) -> int | None` (filter and search, no paging).

For the request-scoped app sources:

```python
class CasesSource(AppDataSourceBase[Registry, CaseRow]):
    supports_search = True

    async def do_fetch(self, registry, user, query):
        return registry.cases.list(apply_sql_query(select(CaseRecord), query, COLUMNS))

    async def do_count(self, registry, user, query):
        return registry.cases.count(apply_sql_filters(select(func.count()).select_from(CaseRecord), query, COLUMNS))
```

The function variants take `count=` and `supports_search=` (`AppReadOnlyDataSource(…, count=count_cases, supports_search=True)`). A source that sets neither keeps working as before: no search field, no numbers on the pills.

Quick filters and search are available on flat tables; a `DataSection` with a hierarchical source raises a `TypeError` when they are given.
