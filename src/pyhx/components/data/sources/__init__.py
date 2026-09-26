"""Data source protocols, query/page models, filter vocabulary, and the
in-memory implementations.

A :class:`ReadOnlyDataSource` / :class:`ReadOnlyHierarchicalDataSource` takes a
:class:`Query` (sort + filter + paging) and returns a :class:`Page` /
:class:`HierarchicalPage` of items. :class:`DataSource` /
:class:`HierarchicalDataSource` extend the read-only protocols with
mutation methods. The filter vocabulary — the per-type operators in
:data:`FilterValue` and the per-field column descriptors in
:data:`FilterType` — is shared between every source and the filter drawer
UI. :class:`SimpleDataSource` / :class:`SimpleHierarchicalDataSource` are
the in-memory implementations used by tests and fixtures; production code
typically wires a database-backed source against the same protocols.
"""

from .app_data_source import (
    AppDataSource,
    AppDataSourceBase,
    AppReadOnlyDataSource,
    AppReadOnlyDataSourceBase,
)
from .app_hierarchical_data_source import (
    AppHierarchicalDataSource,
    AppHierarchicalDataSourceBase,
    AppReadOnlyHierarchicalDataSource,
    AppReadOnlyHierarchicalDataSourceBase,
)
from .filter import (
    BoolIsEmpty,
    BoolIsFalse,
    BoolIsNotEmpty,
    BoolIsTrue,
    Condition,
    DateAfter,
    DateBefore,
    DateBetween,
    DateEquals,
    DateIsEmpty,
    DateIsNotEmpty,
    FilterValue,
    ListContainsAll,
    ListContainsNone,
    ListIntersects,
    ListIsEmpty,
    ListIsNotEmpty,
    NumericBetween,
    NumericEquals,
    NumericGreaterThan,
    NumericGreaterThanOrEqual,
    NumericIsEmpty,
    NumericIsNotEmpty,
    NumericLessThan,
    NumericLessThanOrEqual,
    StringContains,
    StringEndsWith,
    StringEquals,
    StringIsEmpty,
    StringIsNotEmpty,
    StringStartsWith,
    TextChoiceEquals,
    TextChoiceIn,
    TextChoiceIsEmpty,
    TextChoiceIsNotEmpty,
    TextChoiceNotIn,
)
from .filter_type import (
    BooleanFilter,
    ChoiceFilter,
    ChoiceFilterOption,
    DateFilter,
    FilterType,
    ListChoiceFilter,
    NumericFilter,
    TextFilter,
)
from .mapped_data_source import (
    MappedDataSource,
    MappedHierarchicalDataSource,
    MappedReadOnlyDataSource,
    MappedReadOnlyHierarchicalDataSource,
)
from .query import FilterMode, Query
from .simple_data_source import SimpleDataSource
from .simple_hierarchical_data_source import SimpleHierarchicalDataSource
from .sort import SortOrder, SortOrderDirection
from .source import (
    DataSource,
    HierarchicalDataSource,
    HierarchicalPage,
    Node,
    Page,
    ReadOnlyDataSource,
    ReadOnlyHierarchicalDataSource,
)
from .sql_query import (
    ColumnMap,
    apply_sql_filters,
    apply_sql_paging,
    apply_sql_query,
    apply_sql_sort,
    columns_from_model,
)

__all__ = [
    "AppDataSource",
    "AppDataSourceBase",
    "AppHierarchicalDataSource",
    "AppHierarchicalDataSourceBase",
    "AppReadOnlyDataSource",
    "AppReadOnlyDataSourceBase",
    "AppReadOnlyHierarchicalDataSource",
    "AppReadOnlyHierarchicalDataSourceBase",
    "BoolIsEmpty",
    "BoolIsFalse",
    "BoolIsNotEmpty",
    "BoolIsTrue",
    "BooleanFilter",
    "ChoiceFilter",
    "ChoiceFilterOption",
    "ColumnMap",
    "Condition",
    "DataSource",
    "DateAfter",
    "DateBefore",
    "DateBetween",
    "DateEquals",
    "DateFilter",
    "DateIsEmpty",
    "DateIsNotEmpty",
    "FilterMode",
    "FilterType",
    "FilterValue",
    "HierarchicalDataSource",
    "HierarchicalPage",
    "ListChoiceFilter",
    "ListContainsAll",
    "ListContainsNone",
    "ListIntersects",
    "ListIsEmpty",
    "ListIsNotEmpty",
    "MappedDataSource",
    "MappedHierarchicalDataSource",
    "MappedReadOnlyDataSource",
    "MappedReadOnlyHierarchicalDataSource",
    "Node",
    "NumericBetween",
    "NumericEquals",
    "NumericFilter",
    "NumericGreaterThan",
    "NumericGreaterThanOrEqual",
    "NumericIsEmpty",
    "NumericIsNotEmpty",
    "NumericLessThan",
    "NumericLessThanOrEqual",
    "Page",
    "Query",
    "ReadOnlyDataSource",
    "ReadOnlyHierarchicalDataSource",
    "SimpleDataSource",
    "SimpleHierarchicalDataSource",
    "SortOrder",
    "SortOrderDirection",
    "StringContains",
    "StringEndsWith",
    "StringEquals",
    "StringIsEmpty",
    "StringIsNotEmpty",
    "StringStartsWith",
    "TextChoiceEquals",
    "TextChoiceIn",
    "TextChoiceIsEmpty",
    "TextChoiceIsNotEmpty",
    "TextChoiceNotIn",
    "TextFilter",
    "apply_sql_filters",
    "apply_sql_paging",
    "apply_sql_query",
    "apply_sql_sort",
    "columns_from_model",
]
