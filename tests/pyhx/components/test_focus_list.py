"""Render tests for the ``focus_list`` table variant.

Two concerns: (1) the table forwards arbitrary row attributes onto the ``<tr>``
so a caller can opt a row into the data-table clickable / selectable affordance
(``aria-selected`` + their own htmx); (2) each table's header carries a *unique*
``view-transition-name`` so several focus-list tables can share one page — a
duplicate name aborts the whole View Transition.
"""

import re
from pathlib import Path

from pyhx.components.primitives import focus_list

FOCUS_CSS = Path(
    "src/pyhx/static/css/pyhx/components/primitives/focus-list.css"
).read_text()


def _table_html(**row_attrs) -> str:
    columns = [focus_list.table_column("H")]
    row = focus_list.table_row([focus_list.table_cell("cell")], id="r1", **row_attrs)
    return str(focus_list.table(columns, [row]))


def _header_vtn(html: str) -> str:
    m = re.search(r'<thead style="view-transition-name:\s*([^;"]+)', html)
    assert m, "header view-transition-name not found"
    return m.group(1)


def _table_with(*, id=None) -> str:
    columns = [focus_list.table_column("H")]
    row = focus_list.table_row([focus_list.table_cell("cell")], id="r1")
    return str(focus_list.table(columns, [row], id=id))


class TestTableRowAttrs:
    def test_aria_selected_forwarded_to_tr(self) -> None:
        html = _table_html(aria_selected="false")
        assert 'aria-selected="false"' in html

    def test_htmx_attrs_forwarded_to_tr(self) -> None:
        html = _table_html(
            aria_selected="true",
            hx_post="/toggle",
            hx_target="#wrap",
        )
        assert 'aria-selected="true"' in html
        assert 'hx-post="/toggle"' in html
        assert 'hx-target="#wrap"' in html

    def test_extra_class_merges_with_item_class(self) -> None:
        html = _table_html(class_="my-extra")
        # the focus-list item class is still present alongside the caller's class
        assert "hx-focus-list__item" in html
        assert "my-extra" in html

    def test_no_attrs_still_renders_plain_row(self) -> None:
        html = _table_html()
        assert "hx-focus-list__item" in html
        assert "aria-selected" not in html


class TestHeaderViewTransitionName:
    def test_name_is_set_inline_on_thead(self) -> None:
        # Inline (not in CSS) so each instance can carry a distinct name.
        assert _header_vtn(_table_with(id="main")) == "hx-focus-list-header--main"

    def test_distinct_ids_give_distinct_names(self) -> None:
        a = _header_vtn(_table_with(id="main"))
        b = _header_vtn(_table_with(id="selectable"))
        assert a != b

    def test_omitted_id_still_unique_per_render(self) -> None:
        # Two id-less tables on one page must not collide (a duplicate
        # view-transition-name aborts the whole transition).
        assert _header_vtn(_table_with()) != _header_vtn(_table_with())

    def test_no_thead_name_when_header_disabled(self) -> None:
        columns = [focus_list.table_column("H")]
        row = focus_list.table_row([focus_list.table_cell("c")], id="r1")
        html = str(focus_list.table(columns, [row], header=False))
        assert "<thead" not in html


class TestPrimitiveCellClasses:
    def test_focus_list_uses_primitive_cell_classes(self) -> None:
        # Verify the focus-list table emits primitive table cell classes
        # and CSS variables, not the deprecated data-table variants.
        columns = [
            focus_list.table_column("Name"),
            focus_list.table_column("Count", kind="numeric"),
        ]
        cells = [
            focus_list.table_cell("Item A"),
            focus_list.table_cell("42"),
        ]
        row = focus_list.table_row(cells, id="r1")
        html = str(focus_list.table(columns, [row]))

        # Must emit primitive cell classes
        assert "hx-table__cell--numeric" in html
        # Must set primitive grid column variable
        assert "--hx-table--cols" in html
        # Must not contain old data-table class names
        assert "hx-data-table" not in html

    def test_table_carries_primitive_class_and_cols_var(self) -> None:
        columns = [focus_list.table_column("Name")]
        row = focus_list.table_row([focus_list.table_cell("x")], id="r1")
        html = str(focus_list.table(columns, [row]))
        # the grid var and class live on the <table>, not the wrapping div
        assert '<table class="hx-table"' in html
        assert "--hx-table--cols" in html

    def test_body_cell_has_base_primitive_class(self) -> None:
        columns = [focus_list.table_column("Name")]
        row = focus_list.table_row([focus_list.table_cell("x")], id="r1")
        html = str(focus_list.table(columns, [row]))
        # a kind-less cell still gets the primitive base cell class
        assert 'class="hx-table__cell"' in html

    def test_rows_keep_focus_list_item_class(self) -> None:
        columns = [focus_list.table_column("Name")]
        row = focus_list.table_row([focus_list.table_cell("x")], id="r1")
        html = str(focus_list.table(columns, [row]))
        assert "hx-focus-list__item" in html

    def test_colspan_still_emits_grid_column(self) -> None:
        columns = [focus_list.table_column("A"), focus_list.table_column("B")]
        row = focus_list.table_row(
            [focus_list.table_cell("wide", colspan="all")], id="r1"
        )
        html = str(focus_list.table(columns, [row]))
        assert "grid-column: 1 / -1" in html


class TestFocusListCssDedup:
    def test_inherited_grid_rules_removed(self) -> None:
        # These are now inherited from `.hx-table`; must not be re-declared.
        assert "> table > thead," not in FOCUS_CSS  # thead/tbody display:block block
        # the table-variant selectable-row TINT is inherited from the primitive
        assert (
            ".hx-focus-list--variant-table .hx-focus-list__item[aria-selected]:hover > td"
            not in FOCUS_CSS
        )
        # the layout-kind reset is an exact dup of the primitive's
        assert "td.hx-table__cell--layout" not in FOCUS_CSS

    def test_header_override_present(self) -> None:
        # header cells must neutralise the primitive's frosted th chrome…
        assert ".hx-focus-list--variant-table .hx-table thead th" in FOCUS_CSS
        # …while the blur stays on the <thead> (view-transition backdrop root)
        assert ".hx-focus-list--variant-table .hx-table thead" in FOCUS_CSS

    def test_still_consumes_table_sticky_top(self) -> None:
        # scope decision: focus-list keeps this token live
        assert "var(--hx-table--sticky-top)" in FOCUS_CSS

    def test_kept_non_inherited_bits(self) -> None:
        # row padding override + focus behavior must remain
        assert "data-is-active" in FOCUS_CSS          # sibling-dim / active-lift
        assert "view-transition" in FOCUS_CSS          # transitions kept
