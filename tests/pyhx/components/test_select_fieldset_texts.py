"""Checkbox and radio fieldsets show a help or error text below the group, also in a DataForm."""

import asyncio
from typing import Annotated

import htpy as y
from pydantic import BaseModel, field_validator

from pyhx.components import annotations as a
from pyhx.components.data.data_form import DataForm
from pyhx.components.primitives.select_fieldset import checkbox_fieldset, radio_fieldset
from pyhx.components.view_model.options import Option

OPTIONS = [Option(label="Read", value="read"), Option(label="Write", value="write")]


def test_no_text_keeps_the_plain_fieldset():
    html = str(checkbox_fieldset("Rights", "rights", OPTIONS, class_="hx-grid-span-2"))

    assert html.startswith('<fieldset class="hx-select-fieldset hx-grid-span-2"')
    assert "<small" not in html and "aria-invalid" not in html


def test_an_error_text_is_shown_below_and_marks_the_group_invalid():
    html = str(
        checkbox_fieldset(
            "Rights", "rights", OPTIONS, error_text="Pick one.", class_="hx-grid-span-2"
        )
    )

    assert html.startswith('<div class="hx-form-field hx-grid-span-2">')
    assert (
        'aria-invalid="true"' in html and 'aria-describedby="rights__help_text"' in html
    )
    assert '<small id="rights__help_text">Pick one.</small>' in html


def test_the_error_replaces_the_help_text():
    html = str(
        radio_fieldset(
            "Right", "right", OPTIONS, help_text="Choose.", error_text="Wrong."
        )
    )

    assert "Wrong." in html and "Choose." not in html


def test_a_help_text_is_shown_without_marking_the_group_invalid():
    html = str(radio_fieldset("Right", "right", OPTIONS, help_text="Choose."))

    assert (
        '<small id="right__help_text">Choose.</small>' in html
        and "aria-invalid" not in html
    )


class _Fragment:
    def url(self, **kwargs) -> str:
        return "/x"


class _FragmentFactory:
    def add(self, path, method, fn) -> _Fragment:
        return _Fragment()


class _Routes:
    def __init__(self) -> None:
        self.fragment = _FragmentFactory()


async def _noop(value):  # pragma: no cover - never invoked in these tests
    return y.div


class Rights(BaseModel):
    rights: Annotated[
        list[str],
        a.MultiselectChoiceField(
            label="Rights", control=a.CheckboxFieldsetControl(options=OPTIONS)
        ),
    ]
    active: Annotated[bool, a.BooleanField(label="Active")] = True

    @field_validator("rights")
    @classmethod
    def _not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Pick at least one.")
        return value


def test_a_data_form_shows_errors_at_checkbox_fields():
    form = DataForm(routes=_Routes(), name="t", type=Rights, handle_submit=_noop)  # type: ignore[arg-type]

    html = str(
        asyncio.run(
            form.render(
                Rights.model_construct(rights=[], active=True),
                errors={"rights": "Pick at least one.", "active": "Not now."},
                touched={"rights", "active"},
            )
        )
    )

    assert "Pick at least one." in html and "Not now." in html
