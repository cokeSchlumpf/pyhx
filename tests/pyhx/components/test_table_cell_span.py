"""Render tests for the ``span=`` prop on table cells.

`span` maps to a `--hx-table--cell-span` custom property that the stylesheet
turns into `grid-column: span N`. It lives on the shared cell base, so both
`td` and `th` carry it, and it is mutually exclusive with `kind="empty"`
(which already spans every column).
"""

import re

import pytest

from pyhx.components.primitives.table import table


def _style(html: str) -> str | None:
    m = re.search(r'style="([^"]*)"', html)
    return m.group(1) if m else None


class TestSpanRendersCustomProperty:
    def test_td_span_renders_custom_property(self) -> None:
        html = str(table.td(span=3)["x"])
        assert "--hx-table--cell-span: 3" in (_style(html) or "")

    def test_th_span_renders_custom_property(self) -> None:
        html = str(table.th(span=3)["x"])
        assert "--hx-table--cell-span: 3" in (_style(html) or "")

    def test_span_none_emits_no_style(self) -> None:
        html = str(table.td["x"])
        assert "--hx-table--cell-span" not in html
        assert _style(html) is None

    def test_span_merges_with_existing_style(self) -> None:
        html = str(table.td(span=2, style="color: red")["x"])
        style = _style(html) or ""
        assert "color: red" in style
        assert "--hx-table--cell-span: 2" in style

    def test_span_merges_with_trailing_semicolon_style(self) -> None:
        # A caller `style` with a trailing `;` must not produce a double `;;`.
        html = str(table.td(span=2, style="color: red;")["x"])
        style = _style(html) or ""
        assert ";;" not in style
        assert "color: red" in style
        assert "--hx-table--cell-span: 2" in style


class TestSpanRejectsEmptyKind:
    def test_empty_kind_with_span_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            table.td(kind="empty", span=2)

    def test_empty_kind_without_span_is_allowed(self) -> None:
        html = str(table.td(kind="empty")["No records"])
        assert "hx-table__cell--empty" in html
