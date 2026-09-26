"""The FilterDrawer "Sort by" dropdown honors each column's ``sortable`` flag.

Mirrors ``test_filter_drawer_columns.py`` (stub routes; no request context).
A ``sortable=False`` column (e.g. a ``HiddenColumn``) must not be offered as a
sort key, but must still be filterable when it declares a ``filter``.
"""

import asyncio
from typing import Annotated

import htpy as y
from pydantic import BaseModel

import pyhx.components.data.annotations as a
from pyhx.components.data.annotations.reader import read_column_annotations
from pyhx.components.data.filter_drawer import FilterDrawer


class _Model(BaseModel):
    title: Annotated[str, a.TextColumn(label="TitleCol")]  # sortable (default True)
    tags: Annotated[
        list[str],
        a.HiddenColumn(label="TagsCol", sortable=False, filter=a.TextListFilter()),
    ]  # not sortable, but filterable


class _StubFragment:
    def url(self, **kwargs) -> str:
        return "/frag"


class _StubFragments:
    """Minimal stand-in for FragmentFactory: __init__ only calls .add()."""

    def add(self, path, method, fn) -> _StubFragment:
        return _StubFragment()


class _StubRoutes:
    fragment = _StubFragments()


async def _noop_update(query) -> y.Node:  # pragma: no cover - never called here
    return y.div


def _make(**kwargs) -> FilterDrawer:
    return FilterDrawer(_StubRoutes(), "drawer", "state_input", _noop_update, **kwargs)


def _resolve(drawer: FilterDrawer):
    """(columns, columns_by_key, all_fields_options) for the current render."""
    return asyncio.run(drawer._resolve_columns())


def test_read_column_annotations_threads_sortable():
    cols = read_column_annotations(_Model)
    assert cols["title"].sortable is True
    assert cols["tags"].sortable is False


def test_sort_dropdown_excludes_non_sortable_columns():
    drawer = _make(type=_Model)
    _, columns_by_key, all_fields_options = _resolve(drawer)
    sort_html = str(drawer._render_sort([], columns_by_key, all_fields_options))
    assert "TitleCol" in sort_html  # sortable column is offered as a sort key
    assert "TagsCol" not in sort_html  # sortable=False column is hidden from sort


def test_non_sortable_column_is_still_filterable():
    _, columns_by_key, _ = _resolve(_make(type=_Model))
    # sortable=False gates the sort UI only — it must not affect filterability.
    assert columns_by_key["tags"].sortable is False
    assert columns_by_key["tags"].filter_type is not None
    assert columns_by_key["title"].sortable is True
