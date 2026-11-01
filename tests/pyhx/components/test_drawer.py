import re
from pathlib import Path

from pyhx.components.layouts import drawer, drawer_content

DRAWER_CSS = Path("src/pyhx/static/css/pyhx/components/layout/drawer.css").read_text()


class TestDrawer:
    def test_panel_is_focusable_for_the_drawer_script(self):
        html = str(drawer_content("body", title="Edit"))

        assert '<aside id="drawer-content" aria-label="Edit" tabindex="-1"' in html

    def test_open_drawer_has_its_own_z_index(self):
        # Without it, the open (fixed) drawer is a stacking context at level 0
        # and the sticky page header and table header are drawn above it.
        open_rule = re.search(
            r"\.hx-drawer:has\(> aside > section > \*\) \{(.*?)\n\}", DRAWER_CSS, re.S
        )

        assert open_rule is not None
        assert "z-index: var(--hx-z-sidepanel);" in open_rule.group(1)

    def test_backdrop_leaves_the_bars_free(self):
        html = str(drawer(top="3rem", bottom="2rem"))

        assert "--hx--drawer--top: 3rem" in html
        assert "top: var(--hx--drawer--top);" in DRAWER_CSS
        assert "bottom: var(--hx--drawer-bottom);" in DRAWER_CSS
