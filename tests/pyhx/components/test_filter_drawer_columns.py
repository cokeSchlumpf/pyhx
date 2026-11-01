import asyncio

import htpy as y
from pydantic import BaseModel

from pyhx.components.data.filter_drawer import FilterDrawer
from pyhx.components.data.column import Column


class Person(BaseModel):
    name: str
    age: int


class _StubFragments:
    """Minimal stand-in for FragmentFactory: __init__ only calls .add()."""

    def add(self, path, method, fn):
        return None


class _StubRoutes:
    fragment = _StubFragments()


async def _noop_update(query) -> y.Node:  # pragma: no cover - never called here
    return y.div


def _make(**kwargs) -> FilterDrawer:
    return FilterDrawer(
        _StubRoutes(), "drawer", "state_input", _noop_update, **kwargs
    )


def _explicit_column(key: str) -> Column:
    return Column(key=key, label=key.title(), header=key.title(), render=lambda r: "")


def _resolve(drawer: FilterDrawer):
    """(columns, columns_by_key, all_fields_options) for the current render."""
    return asyncio.run(drawer._resolve_columns())


def test_derives_columns_from_type():
    columns, _, _ = _resolve(_make(type=Person))
    assert [c.key for c in columns] == ["name", "age"]


def test_explicit_columns_still_supported():
    actions = _explicit_column("actions")
    columns, _, _ = _resolve(_make(columns=(actions,)))
    assert [c.key for c in columns] == ["actions"]


def test_columns_order_whitelists():
    columns, _, _ = _resolve(_make(type=Person, columns_order=["age"]))
    assert [c.key for c in columns] == ["age"]


def test_columns_are_resolved_per_render_not_at_construction():
    # `columns` accepts a provider so a request can shape the column set; it
    # must only be called when the drawer resolves, not in __init__.
    calls = []

    async def provide():
        calls.append(None)
        return (_explicit_column("actions"),)

    drawer = _make(columns=provide)
    assert calls == []

    columns, _, _ = _resolve(drawer)
    assert [c.key for c in columns] == ["actions"]
    assert len(calls) == 1


def test_columns_by_key_and_field_options_track_resolved_columns():
    _, columns_by_key, all_fields_options = _resolve(_make(type=Person))
    assert set(columns_by_key) == {"name", "age"}
    assert {o.value for o in all_fields_options} == {"name", "age"}
