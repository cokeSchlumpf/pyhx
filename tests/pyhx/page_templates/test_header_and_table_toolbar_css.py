"""The header's dropdowns stay above sticky table headers; the table toolbar can be reached with the pointer."""

import re
from pathlib import Path

CSS = Path("src/pyhx/static/css")
TABLE_CSS = (CSS / "pyhx/components/primitives/table.css").read_text()


def _header_rule(shell: str) -> str:
    css = (CSS / f"page-templates/{shell}.css").read_text()
    match = re.search(r"& > header \{(.*?)\n        \}", css, re.S)
    assert match, shell
    return match.group(1)


def test_page_headers_are_above_sticky_table_headers():
    for shell in ("canvas-shell", "app-shell"):
        rule = _header_rule(shell)
        assert "z-index: var(--hx-z-page-header);" in rule, shell
        assert "--hx-z-table-header" not in rule, shell


def test_the_page_header_layer_is_above_the_table_header_layer():
    theme = (CSS / "pyhx/theme.css").read_text()
    layers = dict(re.findall(r"--hx-z-([a-z-]+):\s*(\d+);", theme))
    assert int(layers["page-header"]) > int(layers["table-header"])


def test_the_toolbar_shows_from_the_filter_bar_too():
    assert ".hx-table__wrapper:has(.hx-table thead:hover, .hx-table__filter-bar:hover) .hx-table__toolbar" in TABLE_CSS


def test_a_strip_bridges_the_gap_between_toolbar_and_table():
    rule = re.search(r"\.hx-table__toolbar::after \{(.*?)\}", TABLE_CSS, re.S)
    assert rule
    assert "top: 100%;" in rule.group(1) and "height: var(--hx-spacing-sm);" in rule.group(1)
    assert 'content: "";' in rule.group(1)
    assert "transform: translateY(calc(-100% - var(--hx-spacing-sm)));" in TABLE_CSS
