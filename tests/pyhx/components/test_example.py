import pytest

from pyhx.components.layouts.example import example


def _html(node):
    return str(node)


def test_example_wraps_preview_and_code_block():
    html = _html(example("PREVIEW", code=[("code", "x()"), ("imports", "import x")]))
    assert "hx-example__preview" in html
    assert "PREVIEW" in html
    # delegates the terminal to the code component
    assert "hx-code__shell" in html
    assert 'name="hx_code__cfg"' in html


def test_example_passes_copy_false_through():
    html = _html(example("p", code=[("only", "1")], copy=False))
    assert "hx-code__copy" not in html


def test_example_passes_max_height_through():
    html = _html(example("p", code=[("only", "1")], max_height="40rem"))
    assert "--hx-code-max-height: 40rem" in html


def test_example_per_part_lang_highlights():
    html = _html(example("p", code=[("code", "def f(): pass", "python")]))
    assert '<span class="k">def</span>' in html


def test_example_validation_bubbles_from_code():
    with pytest.raises(ValueError):
        example("p", code=[])
