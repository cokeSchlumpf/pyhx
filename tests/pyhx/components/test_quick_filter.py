"""Quick filter model and searchable columns (T-008)."""

from typing import Annotated

import pytest
from pydantic import BaseModel

import pyhx.components.data.annotations as a
from pyhx.components.data.annotations.reader import read_column_annotations
from pyhx.components.data.quick_filter import (
    QuickFilter,
    QuickFilters,
    active_quick_filter,
    apply_quick_filter,
)
from pyhx.components.data.sources.filter import (
    Condition,
    StringContains,
    TextChoiceEquals,
    TextChoiceIn,
)
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.sort import SortOrder


def _status(*values: str) -> Condition:
    return Condition(key="status", values=[TextChoiceIn(values=list(values))])


ALL = QuickFilter(key="all", label="All")
OPEN = QuickFilter(key="open", label="Open", filter=[_status("new", "in_progress")])
INPUT = QuickFilter(key="input", label="Requires input", filter=[_status("input")])
FILTERS = QuickFilters(presets=[ALL, OPEN, INPUT])

NAME = Condition(key="name", values=[StringContains(value="mei")])


class TestApply:
    def test_sets_the_preset_conditions(self):
        query = apply_quick_filter(Query(), OPEN, FILTERS)
        assert query.filter == [_status("new", "in_progress")]

    def test_replaces_conditions_on_preset_columns(self):
        query = Query(filter=[_status("closed")])
        assert apply_quick_filter(query, INPUT, FILTERS).filter == [_status("input")]

    def test_keeps_other_columns_sort_and_search(self):
        query = Query(
            filter=[NAME, _status("closed")],
            sort=[SortOrder(key="name", order="desc")],
            search="x",
        )
        result = apply_quick_filter(query, OPEN, FILTERS)
        assert result.filter == [NAME, _status("new", "in_progress")]
        assert result.sort == query.sort
        assert result.search == "x"

    def test_all_removes_preset_conditions_only(self):
        query = Query(filter=[NAME, _status("input")])
        assert apply_quick_filter(query, ALL, FILTERS).filter == [NAME]

    def test_does_not_mutate_the_input(self):
        query = Query(filter=[_status("closed")])
        apply_quick_filter(query, OPEN, FILTERS)
        assert query.filter == [_status("closed")]


class TestActive:
    def test_unfiltered_table_shows_all(self):
        assert active_quick_filter(Query(), FILTERS) is ALL

    def test_matching_conditions_activate_the_preset(self):
        assert active_quick_filter(Query(filter=[_status("input")]), FILTERS) is INPUT

    def test_condition_on_another_column_keeps_the_pill(self):
        query = Query(filter=[NAME, _status("input")])
        assert active_quick_filter(query, FILTERS) is INPUT

    def test_changed_condition_on_a_preset_column_is_custom(self):
        assert active_quick_filter(Query(filter=[_status("closed")]), FILTERS) is None

    def test_other_operator_is_custom(self):
        query = Query(
            filter=[Condition(key="status", values=[TextChoiceEquals(value="input")])]
        )
        assert active_quick_filter(query, FILTERS) is None


class TestValidation:
    def test_duplicate_keys_are_rejected(self):
        with pytest.raises(ValueError, match="unique"):
            QuickFilters(presets=[ALL, QuickFilter(key="all", label="Again")])

    def test_two_conditions_on_one_column_are_rejected(self):
        with pytest.raises(ValueError, match="more than one condition"):
            QuickFilters(
                presets=[
                    QuickFilter(key="x", label="X", filter=[_status("a"), _status("b")])
                ]
            )

    def test_find_and_columns(self):
        assert FILTERS.find("open") is OPEN
        assert FILTERS.find("nope") is None
        assert FILTERS.columns == {"status"}


class Row(BaseModel):
    name: Annotated[str, a.TextColumn(searchable=True)]
    code: Annotated[str, a.TextColumn()]
    plain: str


def test_searchable_flag_reaches_the_column():
    columns = read_column_annotations(Row)
    assert columns["name"].searchable is True
    assert columns["code"].searchable is False
    assert columns["plain"].searchable is False


def test_default_labels_are_translated():
    from pyhx.components.data.quick_filter import TableSearch
    from pyhx.i18n import use_locale

    with use_locale("de"):
        assert str(QuickFilters(presets=[]).label) == "Schnellfilter"
        assert str(TableSearch().label) == "Suchen"
    with use_locale("fr"):
        assert str(TableSearch().label) == "Rechercher"
    assert str(TableSearch().label) == "Search"
