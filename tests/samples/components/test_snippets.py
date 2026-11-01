import textwrap

import pytest

from samples.components._snippets import Snippets, extract_region


SOURCE = textwrap.dedent(
    '''\
    y.article[
        y.h2["All appearances"],
        # docs:start all_appearances
        pill.container(
            *[pill(a, appearance=a) for a in APPEARANCES],
            style="margin-block: 1rem;",
        ),
        # docs:end all_appearances
        y.h2["With value"],
        # docs:start with_value
        pill("Version", value="1.2.0", appearance="neutral"),
        # docs:end with_value
    ]
    '''
)


def test_extracts_region_dedented_flush_left():
    result = extract_region(SOURCE, "all_appearances")
    assert result == (
        'pill.container(\n'
        '    *[pill(a, appearance=a) for a in APPEARANCES],\n'
        '    style="margin-block: 1rem;",\n'
        '),'
    )


def test_extracts_second_region_in_same_file():
    result = extract_region(SOURCE, "with_value")
    assert result == 'pill("Version", value="1.2.0", appearance="neutral"),'


def test_fence_lines_excluded():
    result = extract_region(SOURCE, "all_appearances")
    assert "docs:start" not in result
    assert "docs:end" not in result


def test_missing_name_raises():
    with pytest.raises(KeyError, match="nope"):
        extract_region(SOURCE, "nope")


def test_unbalanced_fence_raises():
    bad = "# docs:start solo\npill('x'),\n"
    with pytest.raises(ValueError, match="solo"):
        extract_region(bad, "solo")


def test_duplicate_name_raises():
    dup = (
        "# docs:start dup\na\n# docs:end dup\n"
        "# docs:start dup\nb\n# docs:end dup\n"
    )
    with pytest.raises(ValueError, match="dup"):
        extract_region(dup, "dup")


def test_getitem_renders_pre_code(tmp_path):
    f = tmp_path / "page.py"
    f.write_text(
        "x = [\n"
        "    # docs:start demo\n"
        "    pill('<ok>'),\n"
        "    # docs:end demo\n"
        "]\n",
        encoding="utf-8",
    )
    node = Snippets(str(f))["demo"]
    html = str(node)
    assert html.startswith("<pre><code>")
    assert html.endswith("</code></pre>")
    # htpy HTML-escapes text, which is correct inside a code block:
    # angle brackets become entities so the snippet displays verbatim.
    assert "&lt;ok&gt;" in html
    assert "<ok>" not in html
