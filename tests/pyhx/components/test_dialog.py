import asyncio
import re
from pathlib import Path

import htpy as y

import pyhx.components as c
from pyhx.components.layouts.dialog import close_dialog

DIALOG_CSS = Path("src/pyhx/static/css/pyhx/components/layout/dialog.css").read_text()
DIALOG_JS = Path("src/pyhx/static/js/pyhx.dialog.js").read_text()
THEME_CSS = Path("src/pyhx/static/css/pyhx/theme.css").read_text()


def _z(name: str) -> int:
    match = re.search(rf"--hx-z-{name}:\s*(\d+);", THEME_CSS)
    assert match is not None
    return int(match.group(1))


class TestDialogContent:
    def test_without_children_it_is_closed_and_empty(self):
        html = str(c.dialog_content())

        assert html == (
            '<dialog id="dialog-content" tabindex="-1" hx-ext="morph" '
            'hx-swap-oob="morph"></dialog>'
        )

    def test_with_children_it_is_open_modal_and_labelled_by_its_title(self):
        html = str(c.dialog_content(y.p["Body"], title="Delete project?"))

        assert '<dialog id="dialog-content" open aria-modal="true"' in html
        assert 'aria-labelledby="dialog-content__title"' in html
        assert '<h2 id="dialog-content__title">Delete project?</h2>' in html
        assert "<section><p>Body</p></section>" in html

    def test_several_children_are_the_content_and_none_alone_is_closed(self):
        html = str(c.dialog_content(y.p["One"], None, y.p["Two"], title="Notice"))

        assert "<section><p>One</p><p>Two</p></section>" in html
        assert " open " not in str(c.dialog_content(None))

    def test_content_and_actions_are_in_one_form(self):
        html = str(
            c.dialog_content(
                y.input(type="checkbox", name="dont_show_again", value="true"),
                title="Notice",
                actions=c.button("Accept", hx_post="/notice/accept", name="choice", value="accept"),
            )
        )

        form = re.search(r'<form class="hx-dialog__form" hx-swap="none">(.*)</form>', html)
        assert form is not None
        assert 'name="dont_show_again"' in form.group(1)
        assert 'hx-post="/notice/accept"' in form.group(1)
        assert "<footer>" in form.group(1)

    def test_closable_dialog_has_a_close_button_that_never_submits(self):
        html = str(c.dialog_content("Body", title="Notice"))

        assert 'aria-label="Close"' in html
        assert 'type="button"' in html
        assert "data-hx-dialog-close" in html
        assert f'hx-post="{close_dialog.url()}"' in html

    def test_close_url_replaces_the_generic_close(self):
        html = str(c.dialog_content("Body", title="Notice", close_url="/notice/close"))

        assert 'hx-post="/notice/close"' in html
        assert close_dialog.url() not in html

    def test_required_dialog_has_no_close_button(self):
        html = str(c.dialog_content("Body", title="Notice", closable=False))

        assert "data-hx-dialog-close" not in html
        assert 'aria-label="Close"' not in html

    def test_close_dialog_returns_an_empty_dialog(self):
        html = str(asyncio.run(close_dialog.render(id="dialog-content")).node)

        assert "<dialog" in html
        assert " open" not in html


class TestDialogMount:
    def test_mount_has_a_backdrop_and_an_empty_dialog(self):
        html = str(c.dialog())

        assert html.startswith('<div class="hx-dialog"><div class="hx-dialog__backdrop" aria-hidden="true">')
        assert '<dialog id="dialog-content"' in html

    def test_open_attributes_load_the_dialog_without_a_target_swap(self):
        attrs = c.open_dialog_htmx_attributes("/projects/1/delete", as_dict=True)

        assert attrs == {"hx_get": "/projects/1/delete", "hx_swap": "none"}

    def test_open_attributes_with_another_method(self):
        attrs = c.open_dialog_htmx_attributes("/x", method="POST", as_dict=True)

        assert attrs["hx_post"] == "/x"


class TestDialogStyles:
    def test_dialog_is_below_the_drawers_and_above_the_page_header(self):
        open_rule = re.search(r"\.hx-dialog:has\(> dialog\[open\]\) \{(.*?)\n\}", DIALOG_CSS, re.DOTALL)

        assert open_rule is not None
        assert "z-index: var(--hx-z-dialog);" in open_rule.group(1)
        assert _z("page-header") < _z("dialog") < _z("sidepanel")

    def test_page_does_not_scroll_while_the_dialog_is_open(self):
        assert "html:has(.hx-dialog > dialog[open])" in DIALOG_CSS

    def test_pico_full_screen_dialog_is_reset(self):
        rule = re.search(r"\n\.hx-dialog > dialog \{(.*?)\n\}", DIALOG_CSS, re.DOTALL)

        assert rule is not None
        for declaration in ("min-width: 0;", "min-height: 0;", "z-index: auto;", "backdrop-filter: none;"):
            assert declaration in rule.group(1)

    def test_actions_stack_at_phone_width(self):
        assert "@media (max-width: 480px)" in DIALOG_CSS
        assert "flex-direction: column-reverse;" in DIALOG_CSS

    def test_stylesheet_is_imported(self):
        assert '@import "./pyhx/components/layout/dialog.css" layer(pyhx);' in Path(
            "src/pyhx/static/css/pyhx.css"
        ).read_text()


class TestDialogScript:
    def test_script_is_loaded_by_the_skeleton(self):
        assert 'script(src="/static/js/pyhx.dialog.js")' in Path("src/pyhx/core/templates/skeleton.py").read_text()

    def test_page_behind_is_inert_except_drawers_and_notifications(self):
        assert "const KEEP = '.hx-dialog, .hx-drawer, .hx-notifications, template, script';" in DIALOG_JS
        assert "el.inert = true" in DIALOG_JS
        assert "before.inerted.forEach((el) => { el.inert = false; });" in DIALOG_JS

    def test_closed_drawers_are_inert_while_the_dialog_is_open(self):
        # A closed drawer is only moved off screen; its close button would
        # otherwise stay in the tab order behind the dialog.
        assert "if (dialogOpen && !open && !drawer.inert)" in DIALOG_JS
        assert "drawer.querySelector(':scope > aside')?.focus(" in DIALOG_JS

    def test_escape_waits_for_drawers_and_needs_a_close_button(self):
        handler = DIALOG_JS[DIALOG_JS.index("addEventListener('keydown'") :]

        assert handler.index("if (isDrawerOpen()) return;") < handler.index("button.click()")
        assert "mount.querySelector('[data-hx-dialog-close]')" in handler

    def test_backdrop_has_no_click_handler(self):
        assert "addEventListener('click'" not in DIALOG_JS

    def test_browser_never_closes_or_submits_on_its_own(self):
        assert "addEventListener('cancel'" in DIALOG_JS
        assert "addEventListener('submit'" in DIALOG_JS

    def test_focus_goes_to_autofocus_or_the_dialog(self):
        assert "dialog.querySelector('[autofocus]') ?? dialog" in DIALOG_JS
