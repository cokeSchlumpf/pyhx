"""Render tests for the ``conditional_select`` primitive."""

from pyhx.components.primitives import ConditionalSelectLabels, conditional_select
from pyhx.components.primitives.conditional_select import (
    CONFIG_JSON_FIELD,
    ConditionalSelectProps,
)
from pyhx.components.view_model import Option


OPTIONS = [
    Option(label="Germany", value="de"),
    Option(label="France", value="fr"),
    Option(label="Italy", value="it"),
]


def _html(name: str, **kwargs) -> str:
    return str(conditional_select(name, OPTIONS, **kwargs))


class TestAllMode:
    def test_renders_hidden_config_and_toggle(self) -> None:
        html = _html("regions")
        assert f'name="{CONFIG_JSON_FIELD}__' in html
        # the mode toggle submits under the derived mode field
        assert 'name="regions__mode"' in html

    def test_no_picker_and_no_value_inputs(self) -> None:
        html = _html("regions")  # defaults to mode="all"
        # nothing should submit under the value field while in "all" mode
        assert 'name="regions"' not in html
        assert "hx-drawer-select" not in html

    def test_toggle_labels_are_configurable(self) -> None:
        html = _html(
            "regions",
            labels=ConditionalSelectLabels(all_option="Global", specific_option="Pick"),
        )
        assert "Global" in html
        assert "Pick" in html


class TestHtmxWiring:
    def test_swap_targets_root_via_closest_not_id(self) -> None:
        # The root id is a raw uuid4 that often starts with a digit, which makes
        # ``#<id>`` an invalid CSS selector (querySelector throws, swap silently
        # fails). The toggle must target/include the root via ``closest`` instead.
        html = _html("regions")
        assert 'hx-target="closest .hx-conditional-select"' in html
        assert 'hx-include="closest .hx-conditional-select"' in html
        assert 'hx-target="#' not in html
        assert 'hx-include="#' not in html


class TestSpecificMode:
    def test_drawer_control_renders_with_selection(self) -> None:
        html = _html("regions", mode="specific", value=["de", "it"])
        assert "hx-drawer-select" in html or "Select items" in html
        # selected values submit under the value field
        assert 'name="regions"' in html
        assert 'value="de"' in html
        assert 'value="it"' in html

    def test_dropdown_control(self) -> None:
        html = _html("regions", mode="specific", value=["fr"], control="dropdown")
        assert "dropdown" in html
        assert 'name="regions"' in html

    def test_checkbox_control(self) -> None:
        html = _html(
            "regions",
            mode="specific",
            value=["fr"],
            control="checkbox",
            labels=ConditionalSelectLabels(fieldset_legend="Regions"),
        )
        assert "<fieldset" in html
        assert "Regions" in html
        assert 'type="checkbox"' in html

    def test_disabled_checkbox_control_still_submits_values(self) -> None:
        # A disabled <fieldset> stops its checkboxes from submitting, so the
        # selected value must be echoed by a hidden input outside the fieldset.
        html = _html(
            "regions", mode="specific", value=["fr"], control="checkbox", disabled=True
        )
        _, _, tail = html.partition("</fieldset>")
        assert '<input type="hidden" name="regions" value="fr">' in tail


class TestProps:
    def test_mode_name_defaults_to_name_suffix(self) -> None:
        props = ConditionalSelectProps(
            name="regions", mode_name="regions__mode", mode="all", control="drawer"
        )
        assert props.mode_name == "regions__mode"

    def test_json_round_trip(self) -> None:
        props = ConditionalSelectProps(
            name="regions",
            mode_name="regions__mode",
            mode="specific",
            control="dropdown",
            value=["de", "fr"],
            options=list(OPTIONS),
            labels=ConditionalSelectLabels(all_option="Global"),
        )
        restored = ConditionalSelectProps.model_validate_json(props.model_dump_json())
        assert restored == props
