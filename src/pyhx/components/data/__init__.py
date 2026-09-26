"""Data-bound components: the data-table primitive, its column types, and
the filter-type vocabulary they accept.

See the submodules for the wider surface — the in-memory ``SimpleDataSource``
lives in :mod:`.sources.simple_data_source`, the discriminated unions of
filter operators in :mod:`.sources.filter`, and the filter drawer in
:mod:`.filter_drawer`.
"""

from ..view_model.columns import ColumnWidth, Fixed, Flex
from . import annotations
from ._model_type import ModelType
from .column import Column
from .data_form import DataForm
from .data_form_drawer import DataFormDrawer
from .data_page import DataPage
from .data_section import DataSection
from .data_table import DataTable
from .filter_drawer import FilterDrawer
from .headless_form import FormRenderContext, HeadlessForm
from .hierarchical_data_table import HierarchicalDataTable
from .sources.filter_type import (
    BooleanFilter,
    ChoiceFilter,
    ChoiceFilterOption,
    DateFilter,
    FilterType,
    ListChoiceFilter,
    NumericFilter,
    TextFilter,
)

__all__ = [
    "BooleanFilter",
    "ChoiceFilter",
    "ChoiceFilterOption",
    "Column",
    "ColumnWidth",
    "DataForm",
    "DataFormDrawer",
    "DataPage",
    "DataSection",
    "DataTable",
    "DateFilter",
    "FilterDrawer",
    "FilterType",
    "Fixed",
    "Flex",
    "FormRenderContext",
    "HeadlessForm",
    "HierarchicalDataTable",
    "ListChoiceFilter",
    "ModelType",
    "NumericFilter",
    "TextFilter",
    "annotations",
]
