"""Render tests for the ``radio_fieldset`` / ``checkbox_fieldset`` primitives.

Focus: a disabled ``<fieldset>`` cascades ``disabled`` to every control inside
it, and a browser never submits a disabled control's value. So the selected
value(s) are echoed by hidden ``<input>`` siblings placed *outside* the
fieldset (a hidden child would be disabled by the cascade too) — otherwise a
disabled required field arrives server-side as missing rather than unchanged.
"""

import re

from pyhx.components.primitives.select_fieldset import (
    checkbox_fieldset,
    radio_fieldset,
)
from pyhx.components.view_model import Option


OPTIONS = [
    Option(label="Germany", value="de"),
    Option(label="France", value="fr"),
    Option(label="Italy", value="it"),
]


def _hidden_inputs(html: str) -> list[str]:
    return re.findall(r'<input type="hidden"[^>]*>', html)


def _after_fieldset(html: str) -> str:
    """The markup that follows the ``</fieldset>`` close tag."""
    _, _, tail = html.partition("</fieldset>")
    return tail


class TestDisabledEmitsHiddenValues:
    def test_radio_emits_single_hidden_value_outside_fieldset(self) -> None:
        html = str(radio_fieldset("L", "country", OPTIONS, value="de", disabled=True))
        hidden = _hidden_inputs(html)
        assert hidden == ['<input type="hidden" name="country" value="de">']
        # The hidden sibling must live outside the disabled fieldset, else the
        # cascade disables it too and it never submits.
        assert 'name="country" value="de"' in _after_fieldset(html)

    def test_checkbox_emits_one_hidden_value_per_selection(self) -> None:
        html = str(
            checkbox_fieldset("L", "country", OPTIONS, value=["de", "it"], disabled=True)
        )
        hidden = _hidden_inputs(html)
        assert hidden == [
            '<input type="hidden" name="country" value="de">',
            '<input type="hidden" name="country" value="it">',
        ]
        tail = _after_fieldset(html)
        assert 'value="de"' in tail and 'value="it"' in tail


class TestNoHiddenValuesOtherwise:
    def test_enabled_emits_no_hidden_inputs(self) -> None:
        html = str(radio_fieldset("L", "country", OPTIONS, value="de", disabled=False))
        assert _hidden_inputs(html) == []

    def test_disabled_without_value_emits_no_hidden_inputs(self) -> None:
        assert (
            _hidden_inputs(str(radio_fieldset("L", "country", OPTIONS, disabled=True)))
            == []
        )
        assert (
            _hidden_inputs(
                str(checkbox_fieldset("L", "country", OPTIONS, disabled=True))
            )
            == []
        )
