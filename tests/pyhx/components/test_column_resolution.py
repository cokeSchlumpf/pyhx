from pydantic import BaseModel

from pyhx.components.data.column_resolution import resolve_columns
from pyhx.components.data.column import Column


class Person(BaseModel):
    name: str
    age: int


def _explicit_column(key: str) -> Column:
    return Column(key=key, label=key.title(), header=key.title(), render=lambda r: "")


def test_derives_columns_from_type():
    cols = resolve_columns(type=Person)
    assert [c.key for c in cols] == ["name", "age"]


def test_explicit_columns_only():
    actions = _explicit_column("actions")
    cols = resolve_columns(explicit=(actions,))
    assert [c.key for c in cols] == ["actions"]


def test_explicit_overrides_derived_on_key_collision():
    custom_name = _explicit_column("name")
    cols = resolve_columns(type=Person, explicit=(custom_name,))
    by_key = {c.key: c for c in cols}
    assert by_key["name"] is custom_name
    assert set(by_key) == {"name", "age"}


def test_columns_order_whitelists_and_reorders():
    cols = resolve_columns(type=Person, columns_order=["age"])
    assert [c.key for c in cols] == ["age"]


def test_no_inputs_yields_empty():
    assert resolve_columns() == ()
