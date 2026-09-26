from pathlib import Path

from pyhx.components import table

CSS = Path("src/pyhx/static/css/pyhx/components/primitives/table.css").read_text()


def test_text_kind_renders_modifier_class():
    html = str(table.td(kind="text")["hi"])
    assert "hx-table__cell--text" in html


def test_body_cells_have_min_height():
    # A1: rows keep the 3em min-height the data table had.
    assert ".hx-table tbody td" in CSS
    assert "min-height: 3em" in CSS


def test_layout_kind_resets_min_height():
    # A --layout cell must drop the min-height so a nested layout owns the box.
    assert "min-height: 0" in CSS


def test_fullscreen_toolbar_transform_reset():
    # A3: in fullscreen the toolbar must not translate off-screen.
    assert "transform: none" in CSS


def test_actions_button_group_right_aligned():
    assert ".hx-table__cell--actions .hx-button-group" in CSS


def test_scrollable_wraps_table_in_scroll_container():
    # `scrollable=True` wraps the <table> in a hx-table__scroll-container so a
    # table wider than its box scrolls within it instead of overflowing.
    html = str(table(scrollable=True)[table.tbody[table.tr[table.td["x"]]]])
    assert "hx-table__scroll-container" in html


def test_not_scrollable_by_default():
    html = str(table[table.tbody[table.tr[table.td["x"]]]])
    assert "hx-table__scroll-container" not in html


def test_scrollable_keeps_controls_outside_scroll_container():
    # The controls/toolbar must stay a direct child of the wrapper (so the
    # absolutely-positioned toolbar stays pinned) rather than scrolling inside
    # the container with the table body.
    html = str(
        table(scrollable=True, controls="MY_TOOLBAR")[
            table.tbody[table.tr[table.td["x"]]]
        ]
    )
    assert "hx-table__scroll-container" in html
    # controls appears before the scroll-container opening tag → sibling, not child
    assert html.index("MY_TOOLBAR") < html.index("hx-table__scroll-container")


def test_no_dead_data_table_assets():
    pyhx_css = Path("src/pyhx/static/css/pyhx.css").read_text()
    assert "data_table.css" not in pyhx_css
    assert not Path("src/pyhx/static/css/pyhx/components/data/data_table.css").exists()
    assert not Path("src/pyhx/static/js/pyhx.data-table.js").exists()
    skeleton = Path("src/pyhx/core/templates/skeleton.py").read_text()
    assert "pyhx.data-table.js" not in skeleton


def test_sticky_top_token_override_sites():
    # Guard test: verify that both contextual override sites set the new
    # --hx-table--sticky-top token alongside the old --data-table--sticky-top.
    # (The root block in app-shell.css already sets both correctly.)
    app_shell = Path("src/pyhx/static/css/page-templates/app-shell.css").read_text()
    page_section = Path("src/pyhx/static/css/pyhx/components/layout/page-section.css").read_text()

    # app-shell.css: the :has(.hx-page-header) rule must set both tokens with the same value
    assert "--hx-table--sticky-top: calc(var(--header--height) + var(--page-header--height))" in app_shell

    # page-section.css: must set both tokens with the same value
    assert "--hx-table--sticky-top: calc(var(--page-section--top) + var(--page-section--header-height))" in page_section
