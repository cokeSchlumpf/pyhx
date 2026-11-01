"""Compact form size (T-006): ``size`` on form_field, DataForm, DataFormDrawer."""

import asyncio

import htpy as y
from pydantic import BaseModel

from pyhx.components import form_field
from pyhx.components.data.data_form import DataForm
from pyhx.components.data.data_form_drawer import DataFormDrawer


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


class _Model(BaseModel):
    name: str


class TestFormField:
    def test_label_text_and_marker_are_wrapped(self):
        html = str(form_field("name", "Name", y.input, required=True))

        assert html.startswith(
            '<label class="hx-form-field"><span class="hx-form-field__label">Name'
            '<span class="hx-form-field__required"> *</span></span><input'
        )

    def test_no_size_by_default(self):
        assert "data-hx-size" not in str(form_field("name", "Name", y.input))

    def test_size_on_the_wrapper(self):
        assert '<label data-hx-size="sm" class="hx-form-field">' in str(
            form_field("name", "Name", y.input, size="sm")
        )
        assert '<div data-hx-size="md" class="hx-form-field">' in str(
            form_field("name", "Name", y.input, size="md", wrapper="div")
        )


class TestDataForm:
    def _form(self, **kwargs) -> DataForm:
        return DataForm(
            routes=_Routes(),  # type: ignore[arg-type]
            name="t",
            type=_Model,
            handle_submit=_noop,
            **kwargs,
        )

    def test_no_size_by_default(self):
        assert "data-hx-size" not in str(asyncio.run(self._form().render()))

    def test_size_on_the_form(self):
        html = str(asyncio.run(self._form(size="sm").render()))

        assert '<form id="hx-data-form__t" data-hx-size="sm"' in html

    def test_drawer_passes_size_and_marks_its_slots(self):
        drawer = DataFormDrawer(
            routes=_Routes(),  # type: ignore[arg-type]
            name="t",
            type=_Model,
            handle_submit=_noop,
            size="md",
        )
        html = str(asyncio.run(drawer.render_drawer(delete_button=y.button["Delete"])))

        assert 'data-hx-size="md"' in html
        assert '<div class="hx-data-form-drawer">' in html
        assert 'class="hx-data-form-drawer__cancel"' in html
        assert (
            '<div class="hx-data-form-drawer__delete"><button>Delete</button>' in html
        )
