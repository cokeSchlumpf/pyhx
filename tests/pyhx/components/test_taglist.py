"""Render tests for the ``taglist`` primitive.

Focus: the selected tags are carried *only* by hidden ``<input>`` elements, so
those must never be disabled — a disabled taglist still has to submit its tags
or saving the form would wipe the selection.
"""

import re

from pyhx.components.primitives.taglist import taglist
from pyhx.components.view_model import Option


OPTIONS = [Option(label="Bug", value="bug"), Option(label="Docs", value="docs")]


def _value_input(html: str, value: str) -> str:
    m = re.search(rf'<input type="hidden" name="tags" value="{value}"[^>]*>', html)
    assert m, f"hidden value input for {value!r} not found"
    return m.group(0)


class TestDisabledStillSubmitsTags:
    def test_value_input_is_not_disabled_when_taglist_disabled(self) -> None:
        html = str(taglist("tags", OPTIONS, value=["bug"], disabled=True))
        # The value-carrying hidden input must submit regardless of disabled state.
        assert "disabled" not in _value_input(html, "bug")

    def test_all_selected_values_present_when_disabled(self) -> None:
        html = str(taglist("tags", OPTIONS, value=["bug", "docs"], disabled=True))
        assert "disabled" not in _value_input(html, "bug")
        assert "disabled" not in _value_input(html, "docs")
