from typing import Annotated

from pydantic import BaseModel

from pyhx.components.data.annotations.column import (
    BooleanFilter,
    DateFilter,
    HiddenColumn,
    MultipleChoiceFilter,
    NumericFilter,
    TextChoiceFilter,
    TextFilter,
    TextListFilter,
)
from pyhx.components.data.annotations.reader import read_column_annotations
from pyhx.components.data.sources.filter_type import (
    BooleanFilter as BooleanFilterT,
    ChoiceFilter as ChoiceFilterT,
    DateFilter as DateFilterT,
    ListChoiceFilter as ListChoiceFilterT,
    NumericFilter as NumericFilterT,
    TextFilter as TextFilterT,
)
from pyhx.components.view_model import Option


def _make_options():
    return (Option(label="A", value="a"), Option(label="B", value="b"))


class Model(BaseModel):
    text: Annotated[str, HiddenColumn(filter=TextFilter())]
    num: Annotated[int, HiddenColumn(filter=NumericFilter())]
    when: Annotated[str, HiddenColumn(filter=DateFilter())]
    flag: Annotated[str, HiddenColumn(filter=BooleanFilter())]
    choice: Annotated[
        str, HiddenColumn(filter=TextChoiceFilter(options=_make_options()))
    ]
    multi: Annotated[
        str, HiddenColumn(filter=MultipleChoiceFilter(options=_make_options()))
    ]
    tags: Annotated[
        list[str], HiddenColumn(filter=TextListFilter(options=_make_options()))
    ]
    plain: Annotated[str, HiddenColumn()]


def test_hidden_columns_are_never_visible():
    cols = read_column_annotations(Model)
    assert all(c.visible is False for c in cols.values())


def test_text_filter_marker_maps_to_text_filter_type():
    cols = read_column_annotations(Model)
    assert isinstance(cols["text"].filter_type, TextFilterT)


def test_numeric_filter_marker_maps_to_numeric_filter_type():
    cols = read_column_annotations(Model)
    assert isinstance(cols["num"].filter_type, NumericFilterT)


def test_date_filter_marker_maps_to_date_filter_type():
    cols = read_column_annotations(Model)
    assert isinstance(cols["when"].filter_type, DateFilterT)


def test_boolean_filter_marker_maps_to_boolean_filter_type():
    cols = read_column_annotations(Model)
    assert isinstance(cols["flag"].filter_type, BooleanFilterT)


def test_choice_filter_marker_materializes_choices():
    cols = read_column_annotations(Model)
    ft = cols["choice"].filter_type
    assert isinstance(ft, ChoiceFilterT)
    assert [(c.label, c.value) for c in ft.choices] == [("A", "a"), ("B", "b")]


def test_multiple_choice_marker_maps_to_multi_choice_filter_type():
    cols = read_column_annotations(Model)
    ft = cols["multi"].filter_type
    assert isinstance(ft, ChoiceFilterT)
    assert ft.multiple is True
    assert [(c.label, c.value) for c in ft.choices] == [("A", "a"), ("B", "b")]


def test_text_list_marker_maps_to_list_choice_filter_type():
    cols = read_column_annotations(Model)
    ft = cols["tags"].filter_type
    assert isinstance(ft, ListChoiceFilterT)
    assert [(c.label, c.value) for c in ft.choices] == [("A", "a"), ("B", "b")]


def test_default_hidden_column_is_unfilterable():
    cols = read_column_annotations(Model)
    assert cols["plain"].filter_type is None


def test_callable_choice_provider_is_lazy():
    def provider():
        return _make_options()

    class LazyModel(BaseModel):
        choice: Annotated[str, HiddenColumn(filter=TextChoiceFilter(options=provider))]

    cols = read_column_annotations(LazyModel)
    ft = cols["choice"].filter_type
    assert isinstance(ft, ChoiceFilterT)
    assert ft._choices_provider is provider
    assert ft.choices == []
