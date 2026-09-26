"""Multiple-choice filters, filter control selection, and ``TextListColumn``."""

from enum import Enum
from typing import Annotated

from commons.dict_operators import unflatten
from pydantic import BaseModel

from pyhx.components.data.annotations.column import (
    MultipleChoiceFilter,
    TextColumn,
    TextListColumn,
    TextListFilter,
)
from pyhx.components.data.annotations.controls import (
    CheckboxFieldsetControl,
    DropdownControl,
)
from pyhx.components.data.annotations.reader import read_column_annotations
from pyhx.components.data.filter_drawer_value import FilterDrawerValue
from pyhx.components.data.sources._query import _matches_value
from pyhx.components.data.sources.filter import (
    ListContainsAll,
    ListContainsNone,
    ListIntersects,
    ListIsEmpty,
    ListIsNotEmpty,
    TextChoiceIn,
    TextChoiceNotIn,
)
from pyhx.components.data.sources.filter_options import get_options_for_type
from pyhx.components.data.sources.filter_type import ChoiceFilter, ListChoiceFilter
from pyhx.components.view_model import Option


OPTIONS = (Option(label="Open", value="open"), Option(label="Closed", value="closed"))


class Status(Enum):
    OPEN = "open"
    CLOSED = "closed"


# --------------------------------------------------------------------------- #
# Filter value coercion & matching
# --------------------------------------------------------------------------- #


def test_text_choice_in_coerces_scalar_and_missing():
    assert TextChoiceIn(values="open").values == ["open"]
    assert TextChoiceIn.model_validate({"kind": "text_choice_in"}).values == []


def test_text_choice_in_membership():
    assert _matches_value("open", TextChoiceIn(values=["open", "closed"])) is True
    assert _matches_value("draft", TextChoiceIn(values=["open"])) is False


def test_text_choice_not_in_exclusion():
    assert _matches_value("draft", TextChoiceNotIn(values=["open", "closed"])) is True
    assert _matches_value("open", TextChoiceNotIn(values=["open"])) is False


def test_empty_selection_is_no_constraint():
    # An unselected multi-filter must not hide every row.
    assert _matches_value("anything", TextChoiceIn(values=[])) is True
    assert _matches_value("anything", TextChoiceNotIn(values=[])) is True
    assert _matches_value(["x"], ListIntersects(values=[])) is True
    assert _matches_value(["x"], ListContainsAll(values=[])) is True
    assert _matches_value(["x"], ListContainsNone(values=[])) is True


def test_list_intersects_semantics():
    assert _matches_value(["a", "b"], ListIntersects(values=["b", "c"])) is True
    assert _matches_value(["a"], ListIntersects(values=["z"])) is False
    assert _matches_value(None, ListIntersects(values=["b"])) is False


def test_list_contains_all_semantics():
    # Row list must be a superset of the selection.
    assert _matches_value(["a", "b", "c"], ListContainsAll(values=["a", "b"])) is True
    assert _matches_value(["a"], ListContainsAll(values=["a", "b"])) is False
    assert _matches_value(None, ListContainsAll(values=["a"])) is False


def test_list_contains_none_semantics():
    # Row list must be disjoint from the selection.
    assert _matches_value(["a", "b"], ListContainsNone(values=["c", "d"])) is True
    assert _matches_value(["a", "b"], ListContainsNone(values=["b"])) is False
    assert _matches_value(None, ListContainsNone(values=["a"])) is True


def test_list_empty_predicates():
    assert _matches_value([], ListIsEmpty()) is True
    assert _matches_value(None, ListIsEmpty()) is True
    assert _matches_value(["x"], ListIsEmpty()) is False
    assert _matches_value(["x"], ListIsNotEmpty()) is True
    assert _matches_value([], ListIsNotEmpty()) is False


# --------------------------------------------------------------------------- #
# Operator options offered per filter type
# --------------------------------------------------------------------------- #


def test_single_choice_operator_options():
    values = [o.value for o in get_options_for_type(ChoiceFilter(multiple=False))]
    assert values == [
        "text_choice_equals",
        "text_choice_is_empty",
        "text_choice_is_not_empty",
    ]


def test_multiple_choice_operator_options_include_negation():
    values = [o.value for o in get_options_for_type(ChoiceFilter(multiple=True))]
    assert values == [
        "text_choice_in",
        "text_choice_not_in",
        "text_choice_is_empty",
        "text_choice_is_not_empty",
    ]


def test_list_operator_options_include_all_and_none():
    values = [o.value for o in get_options_for_type(ListChoiceFilter())]
    assert values == [
        "list_intersects",
        "list_contains_all",
        "list_contains_none",
        "list_is_empty",
        "list_is_not_empty",
    ]


# --------------------------------------------------------------------------- #
# Reader derivation
# --------------------------------------------------------------------------- #


class Row(BaseModel):
    name: str
    status: Annotated[
        str,
        TextColumn(
            filter=MultipleChoiceFilter(
                control=CheckboxFieldsetControl(options=OPTIONS)
            )
        ),
    ]
    labels: Annotated[
        list[str],
        TextListColumn(filter=TextListFilter(control=DropdownControl(options=OPTIONS))),
    ]
    tags: list[str]
    kinds: list[Status]


def test_multiple_choice_filter_records_control_and_multiplicity():
    ft = read_column_annotations(Row)["status"].filter_type
    assert isinstance(ft, ChoiceFilter)
    assert ft.multiple is True
    assert isinstance(ft._control, CheckboxFieldsetControl)
    assert [c.value for c in ft.choices] == ["open", "closed"]


def test_text_list_column_records_control():
    ft = read_column_annotations(Row)["labels"].filter_type
    assert isinstance(ft, ListChoiceFilter)
    assert isinstance(ft._control, DropdownControl)
    assert [c.value for c in ft.choices] == ["open", "closed"]


def test_bare_list_str_auto_derives_pill_column():
    col = read_column_annotations(Row)["tags"]
    assert col.kind == "list"
    assert isinstance(col.filter_type, ListChoiceFilter)
    # No derivable options for free-form list[str].
    assert col.filter_type.choices == []


def test_list_enum_auto_derives_options_and_pills():
    cols = read_column_annotations(Row)
    ft = cols["kinds"].filter_type
    assert isinstance(ft, ListChoiceFilter)
    assert [c.value for c in ft.choices] == ["open", "closed"]


def test_list_cell_renders_pills():
    col = read_column_annotations(Row)["tags"]
    r = Row(name="a", status="open", labels=["open"], tags=["x", "y"], kinds=[])
    html = str(col.render(r))
    assert "hx-pill-container" in html
    assert html.count("hx-pill__label") == 2
    assert ">x<" in html and ">y<" in html


def test_list_enum_cell_renders_enum_values_not_repr():
    col = read_column_annotations(Row)["kinds"]
    r = Row(
        name="a", status="open", labels=[], tags=[], kinds=[Status.OPEN, Status.CLOSED]
    )
    html = str(col.render(r))
    assert ">open<" in html and ">closed<" in html
    assert "Status." not in html


# --------------------------------------------------------------------------- #
# Drawer parse round-trip — the linchpin (repeated checkbox names → list)
# --------------------------------------------------------------------------- #


def _group_multi_items(items):
    """Reproduce the drawer's ``form.multi_items()`` grouping."""
    grouped: dict[str, str | list[str]] = {}
    for key, raw in items:
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = raw
        elif isinstance(existing, list):
            existing.append(raw)
        else:
            grouped[key] = [existing, raw]
    return grouped


def test_multi_select_submission_preserves_all_values():
    items = [
        ("origin", "drawer"),
        ("filter_mode", "all"),
        ("filter[0].key", "status"),
        ("filter[0].values[0].kind", "text_choice_in"),
        ("filter[0].values[0].values", "open"),
        ("filter[0].values[0].values", "closed"),
    ]
    fdv = FilterDrawerValue.model_validate(unflatten(_group_multi_items(items)))
    cond = fdv.filter[0].values[0]
    assert isinstance(cond, TextChoiceIn)
    assert cond.values == ["open", "closed"]


def test_single_checkbox_submission_coerces_to_list():
    items = [
        ("filter[0].key", "status"),
        ("filter[0].values[0].kind", "text_choice_in"),
        ("filter[0].values[0].values", "open"),
    ]
    fdv = FilterDrawerValue.model_validate(unflatten(_group_multi_items(items)))
    assert fdv.filter[0].values[0].values == ["open"]


def test_zero_checkboxes_submission_defaults_to_empty():
    items = [
        ("filter[0].key", "status"),
        ("filter[0].values[0].kind", "text_choice_in"),
    ]
    fdv = FilterDrawerValue.model_validate(unflatten(_group_multi_items(items)))
    assert fdv.filter[0].values[0].values == []


def test_list_contains_all_submission_round_trips():
    items = [
        ("filter[0].key", "tags"),
        ("filter[0].values[0].kind", "list_contains_all"),
        ("filter[0].values[0].values", "server"),
        ("filter[0].values[0].values", "cloud"),
    ]
    fdv = FilterDrawerValue.model_validate(unflatten(_group_multi_items(items)))
    cond = fdv.filter[0].values[0]
    assert isinstance(cond, ListContainsAll)
    assert cond.values == ["server", "cloud"]
