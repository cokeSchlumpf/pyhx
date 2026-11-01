import re

import htpy as y
import pytest

from pyhx.components.layouts.code import (
    CodeConfig,
    CodePart,
    _render_lines,
    _shell,
    code,
    serve_part,
)


def _html(nodes) -> str:
    return str(y.div[nodes])


def test_plain_when_lang_none():
    html = _html(_render_lines("a\nb", None))
    assert html.count("hx-code__line") == 2
    # no token spans
    assert "<span class=\"k\"" not in html


def test_plain_for_explicit_plaintext_values():
    for lang in ("none", "plaintext", "text"):
        html = _html(_render_lines("def f(): pass", lang))
        assert "hx-code__line" in html
        assert "<span class=\"k\"" not in html


def test_python_highlighting_emits_token_classes():
    html = _html(_render_lines("def f(): pass", "python"))
    assert '<span class="k">def</span>' in html
    assert '<span class="nf">f</span>' in html
    # one source line -> one line span
    assert html.count("hx-code__line") == 1


def test_multiline_token_stays_per_line():
    src = '"""a\nb"""'
    html = _html(_render_lines(src, "python"))
    # two source lines, each its own line span
    assert html.count("hx-code__line") == 2
    # the string/docstring class (sd) appears on both lines
    # (Pygments 2.19 lexes triple-quoted strings as Token.Literal.String.Doc -> "sd")
    assert html.count('class="sd"') >= 2


def test_trailing_newline_line_count_consistent_plain_and_highlighted():
    # A single trailing newline is normalized so both paths agree.
    assert _html(_render_lines("a\nb\n", None)).count("hx-code__line") == 2
    assert _html(_render_lines("a\nb\n", "python")).count("hx-code__line") == 2
    # and without a trailing newline they also agree
    assert _html(_render_lines("a\nb", None)).count("hx-code__line") == 2
    assert _html(_render_lines("a\nb", "python")).count("hx-code__line") == 2


def test_unknown_lang_falls_back_to_plain():
    html = _html(_render_lines("def f(): pass", "bogus-lang"))
    assert "hx-code__line" in html
    assert "<span class=\"k\"" not in html


def test_code_renders_shell_and_hidden_config():
    html = str(code([("code", "x()"), ("imports", "import x")]))
    assert "hx-code__shell" in html
    assert 'name="hx_code__cfg"' in html


def test_code_tabs_are_real_buttons_first_active():
    html = str(code([("a", "1"), ("b", "2")]))
    tabs = re.findall(r"<button[^>]*hx-code__tab[^>]*>", html)
    assert len(tabs) == 2
    assert "is-active" in tabs[0]
    assert "is-active" not in tabs[1]


def test_code_tab_htmx_wiring():
    html = str(code([("a", "1"), ("b", "2")]))
    assert serve_part.url() in html
    assert 'hx-target="closest .hx-code__shell"' in html
    assert "transition:true" in html
    assert 'hx-include="closest .hx-code"' in html


def test_single_part_no_bar_docks_copy():
    html = str(code([("only", "1")]))
    assert "hx-code__tab" not in html
    assert "hx-code__bar" not in html
    assert "hx-code__copy-dock" in html
    assert "hx-code__copy" in html


def test_single_part_without_copy_has_no_bar_or_dock():
    html = str(code([("only", "1")], copy=False))
    assert "hx-code__bar" not in html
    assert "hx-code__copy-dock" not in html
    assert "hx-code__copy" not in html


def test_max_height_custom_property_and_none():
    assert "--hx-code-max-height: 30rem" in str(code([("a", "1")], max_height="30rem"))
    assert "--hx-code-max-height" not in str(code([("a", "1")], max_height=None))


def test_per_part_lang_highlights_only_that_part():
    cfg = CodeConfig(
        parts=[
            CodePart(label="py", source="def f(): pass", lang="python"),
            CodePart(label="plain", source="def f(): pass", lang=None),
        ],
        show_copy=True,
    )
    html_py = str(y.div[_shell(cfg, "py")])
    html_plain = str(y.div[_shell(cfg, "plain")])
    assert '<span class="k">def</span>' in html_py
    assert '<span class="k">def</span>' not in html_plain


def test_validation_errors():
    with pytest.raises(ValueError, match="at least one"):
        code([])
    with pytest.raises(ValueError, match="unique"):
        code([("a", "1"), ("a", "2")])


def test_three_tuple_part_carries_lang():
    html = str(code([("a", "def f(): pass", "python")]))
    assert '<span class="k">def</span>' in html


def test_c_code_export_resolves():
    import pyhx.components as c
    assert callable(c.code)
