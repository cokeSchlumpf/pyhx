"""Render tests for the ``text_diff`` primitive."""

import re

from pyhx.components.primitives import text_diff


def _html(old: str, current: str, **kwargs) -> str:
    return str(text_diff(old, current, **kwargs))


def test_identical_strings_have_no_markers() -> None:
    html = _html("the quick brown fox", "the quick brown fox")
    assert "<ins" not in html
    assert "<del" not in html
    assert html.count("the quick brown fox") == 1


def test_pure_insertion_marks_ins_only() -> None:
    html = _html("the brown fox", "the quick brown fox")
    assert "hx-text-diff__ins" in html
    assert "hx-text-diff__del" not in html


def test_pure_deletion_marks_del_only() -> None:
    html = _html("the quick brown fox", "the brown fox")
    assert "hx-text-diff__del" in html
    assert "hx-text-diff__ins" not in html


def test_replacement_marks_both() -> None:
    html = _html("the quick brown fox", "the slow brown fox")
    assert "hx-text-diff__del" in html
    assert "hx-text-diff__ins" in html
    assert "quick" in html
    assert "slow" in html


def test_blank_line_starts_new_paragraph() -> None:
    html = _html("first\n\nsecond", "first\n\nsecond")
    assert html.count('class="hx-text-diff__line"') == 2
    assert "<br>" not in html


def test_single_newline_is_break_within_paragraph() -> None:
    html = _html("first\nsecond", "first\nsecond")
    assert html.count('class="hx-text-diff__line"') == 1
    assert "<br>" in html


def test_no_inline_styles_or_hex_colors() -> None:
    html = _html("the quick brown fox", "the slow brown fox")
    assert "style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{3,6}", html)


def test_spacing_preserved_in_equal_run() -> None:
    html = _html("a  b", "a  b c")
    assert "a  b" in html


def test_container_class_and_extra_kwargs() -> None:
    html = _html("a", "b", class_="extra")
    assert "hx-text-diff" in html
    assert "extra" in html


def test_plain_mode_escapes_html_tags() -> None:
    html = _html("<b>a</b>", "<b>a</b>")
    # Default: input is treated as text, so tags are escaped, not rendered.
    assert "&lt;b&gt;" in html
    assert "<b>" not in html


def test_html_mode_renders_markup() -> None:
    html = _html("<b>a</b>", "<b>a</b>", html=True)
    # html=True: unchanged markup is emitted as-is rather than escaped.
    assert "<b>a</b>" in html
    assert "&lt;b&gt;" not in html


def test_html_mode_keeps_diff_markers() -> None:
    html = _html("<p>the quick fox</p>", "<p>the slow fox</p>", html=True)
    assert "hx-text-diff__del" in html
    assert "hx-text-diff__ins" in html
    assert "quick" in html
    assert "slow" in html


def test_html_mode_markers_never_contain_tags() -> None:
    # A change spanning two paragraphs must not put a <p>/</p> inside an ins/del.
    html = _html("<p>one</p><p>two</p>", "<p>uno</p>", html=True)
    for inner in re.findall(r"<(?:ins|del)\b[^>]*>(.*?)</(?:ins|del)>", html):
        assert "<" not in inner  # no tag ever wrapped by a marker


def test_html_mode_drops_deleted_tags_keeps_current_structure() -> None:
    # Second paragraph removed: its text shows as <del>, its tags do not survive.
    html = _html("<p>one</p><p>two</p>", "<p>one</p>", html=True)
    assert html.count("<p>") == 1
    assert "hx-text-diff__del" in html and "two" in html


def test_html_mode_marks_text_moved_into_new_block() -> None:
    # A paragraph turned into a list item: the words are unchanged, but they now
    # live in a new block, so the list text is marked inserted (and rendered).
    html = _html("<p>buy milk</p>", "<ul><li>buy milk</li></ul>", html=True)
    assert "<ul><li>" in html
    assert re.search(r'<li><ins class="hx-text-diff__ins">buy milk</ins>', html)


def test_html_mode_inline_formatting_is_not_a_text_change() -> None:
    # Bolding a word changes inline structure, not the block context: the word is
    # rendered bold but not marked as inserted/deleted text.
    html = _html("the quick fox", "the <b>quick</b> fox", html=True)
    assert "<b>quick</b>" in html
    assert "hx-text-diff__ins" not in html
    assert "hx-text-diff__del" not in html


def test_html_mode_literal_angle_brackets_are_text_not_tags() -> None:
    # A literal ``<`` ... ``>`` in prose must not be swallowed as a phantom tag;
    # the words inside stay diffable text, and the brackets are escaped as valid
    # HTML (``&lt;``/``&gt;``) rather than emitted as raw markup.
    html = _html("<p>a < b and c > d end</p>", "<p>a < b and c > d done</p>", html=True)
    assert "a &lt; b and c &gt; d" in html
    # Only the genuinely changed word is marked.
    assert re.search(r'<del class="hx-text-diff__del">end</del>', html)
    assert re.search(r'<ins class="hx-text-diff__ins">done</ins>', html)


def test_html_mode_literal_angle_brackets_not_dropped_on_delete() -> None:
    # Text inside a literal ``<`` ... ``>`` span must not be lost when deleted.
    html = _html("<p>keep if a < b and c > d end</p>", "<p>keep end</p>", html=True)
    assert "b and c" in html


def test_html_mode_stray_less_than_is_preserved() -> None:
    # A bare ``<`` with no closing ``>`` must survive tokenisation (escaped).
    html = _html("<p>3 < 5 today</p>", "<p>3 < 5 today</p>", html=True)
    assert "3 &lt; 5 today" in html
    assert "hx-text-diff__ins" not in html and "hx-text-diff__del" not in html


def test_html_mode_entity_vs_literal_quote_is_not_a_diff() -> None:
    # ``&quot;`` and ``"`` render identically, so they must not diff.
    html = _html("<p>she said &quot;hi&quot;</p>", '<p>she said "hi"</p>', html=True)
    assert "hx-text-diff__ins" not in html
    assert "hx-text-diff__del" not in html


def test_html_mode_entity_vs_literal_apostrophe_is_not_a_diff() -> None:
    html = _html("<p>it&#39;s fine</p>", "<p>it's fine</p>", html=True)
    assert "hx-text-diff__ins" not in html
    assert "hx-text-diff__del" not in html


def test_html_mode_entity_vs_literal_ampersand_is_not_a_diff() -> None:
    html = _html("<p>a &amp; b</p>", "<p>a & b</p>", html=True)
    assert "hx-text-diff__ins" not in html
    assert "hx-text-diff__del" not in html


def test_html_mode_nbsp_entity_vs_literal_is_not_a_diff() -> None:
    # ``&nbsp;`` and a literal U+00A0 render identically. They also fall on
    # different token boundaries (entity glues to the word, literal splits off as
    # whitespace), so this only stays diff-free if text is decoded before
    # tokenising.
    html = _html("<p>the FSP&nbsp; end</p>", "<p>the FSP\xa0 end</p>", html=True)
    assert "hx-text-diff__ins" not in html
    assert "hx-text-diff__del" not in html


def test_html_mode_nbsp_only_real_change_is_marked() -> None:
    # Mixed &nbsp;/literal spacing around a genuine word change: only the changed
    # word is marked, the surrounding non-breaking spaces are not.
    html = _html(
        "<p>at the initiative of the FSP&nbsp; end</p>",
        "<p>at the initiative of the FSP\xa0 start</p>",
        html=True,
    )
    assert re.search(r'<del class="hx-text-diff__del">end</del>', html)
    assert re.search(r'<ins class="hx-text-diff__ins">start</ins>', html)
    assert html.count("hx-text-diff__del") == 1
    assert html.count("hx-text-diff__ins") == 1
