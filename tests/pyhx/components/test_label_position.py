"""Label position and form size (T-006): markup, forwarding and CSS rules.

The layout itself (label left while the field's cell is >= 360px) is a
container query; these tests pin the markup it keys off and the rules.
"""

import asyncio
import re
from itertools import product
from pathlib import Path
from typing import Annotated

import htpy as y
import pytest
from pydantic import BaseModel, Field

from pyhx.components import DataPage, form_field
from pyhx.components import annotations as a
from pyhx.components.data.data_form import DataForm
from pyhx.components.data.data_form_drawer import DataFormDrawer
from pyhx.components.data.data_section import DataSection
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core import WebAppRouter

CSS = Path("src/pyhx/static/css/pyhx/components")
FORM_FIELD_CSS = (CSS / "primitives/form_field.css").read_text()
DATA_FORM_CSS = (CSS / "data/data_form.css").read_text()
DRAWER_CSS = (CSS / "layout/drawer.css").read_text()

SIZES = [None, "sm", "md"]
POSITIONS = [None, "top", "left"]


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


class _One(BaseModel):
    name: str
    city: str


@a.form(columns=2)
class _Two(BaseModel):
    name: str
    city: str


@a.form(template_areas=["name city"])
class _Areas(BaseModel):
    name: str
    city: str


class _Item(BaseModel):
    id: Annotated[str, a.HiddenField(), a.HiddenColumn()] = Field(default="1")
    name: str


def _attrs(size, position) -> list[str]:
    return [
        *([f'data-hx-size="{size}"'] if size else []),
        *([f'data-hx-label-position="{position}"'] if position else []),
    ]


class TestFormField:
    @pytest.mark.parametrize(
        ("size", "position", "wrapper"), product(SIZES, POSITIONS, ["label", "div"])
    )
    def test_size_and_position_on_the_wrapper(self, size, position, wrapper):
        html = str(
            form_field(
                "name",
                "Name",
                y.input,
                size=size,
                label_position=position,
                wrapper=wrapper,
            )
        )
        opening = html[: html.index(">") + 1]

        assert opening.startswith(f"<{wrapper}")
        for attr in _attrs(size, position):
            assert attr in opening
        if position is None:
            assert "data-hx-label-position" not in html
        assert 'class="hx-form-field__label"' in html


class TestDataForm:
    @pytest.mark.parametrize(
        ("model", "size", "position"), product([_One, _Two, _Areas], SIZES, POSITIONS)
    )
    def test_size_and_position_on_the_form_keep_the_layout(self, model, size, position):
        form = DataForm(
            routes=_Routes(),  # type: ignore[arg-type]
            name="t",
            type=model,
            handle_submit=_noop,
            size=size,
            label_position=position,
        )
        html = str(asyncio.run(form.render()))
        opening = html[: html.index(">") + 1]

        for attr in _attrs(size, position):
            assert attr in opening
        # The columns and template areas are the form's own; the label
        # position never replaces them.
        if model is _Two:
            assert "--hx-grid-columns: 2" in html
        if model is _Areas:
            assert "grid-template-areas: &#39;name city&#39;" in html
            assert 'class="hx-data-form__cell"' in html

    @pytest.mark.parametrize(("size", "position"), product(SIZES, POSITIONS))
    def test_drawer_passes_both_to_its_form(self, size, position):
        drawer = DataFormDrawer(
            routes=_Routes(),  # type: ignore[arg-type]
            name="t",
            type=_Two,
            handle_submit=_noop,
            size=size,
            label_position=position,
        )
        html = str(asyncio.run(drawer.render_drawer()))

        assert (drawer.form.size, drawer.form.label_position) == (size, position)
        for attr in _attrs(size, position):
            assert attr in html


class TestForwarding:
    @pytest.mark.parametrize(("size", "position"), product(SIZES, POSITIONS))
    def test_data_section_passes_both_to_edit_and_create(self, size, position):
        section = DataSection(
            routes=WebAppRouter(),
            path="/items",
            source=SimpleDataSource([_Item(name="a")]),
            type=_Item,
            form_size=size,
            form_label_position=position,
        )

        for drawer in (section.edit_form, section.create_form):
            assert (drawer.form.size, drawer.form.label_position) == (size, position)

    def test_data_page_passes_both_to_its_section(self):
        page = DataPage(
            routes=WebAppRouter(),
            path="/items",
            source=SimpleDataSource([_Item(name="a")]),
            type=_Item,
            form_size="sm",
            form_label_position="top",
        )

        for drawer in (page.section.edit_form, page.section.create_form):
            assert (drawer.form.size, drawer.form.label_position) == ("sm", "top")

    def test_defaults_leave_both_unset(self):
        page = DataPage(
            routes=WebAppRouter(),
            path="/items",
            source=SimpleDataSource([_Item(name="a")]),
            type=_Item,
        )

        assert page.section.edit_form.form.size is None
        assert page.section.edit_form.form.label_position is None


class TestRules:
    def test_label_left_is_measured_on_the_field(self):
        assert "container-type: inline-size;" in FORM_FIELD_CSS
        assert "@container (min-width: 360px)" in FORM_FIELD_CSS
        # No container on the place any more (the drawer panel or the aside).
        assert "hx-compact" not in FORM_FIELD_CSS

    def test_label_left_is_not_scoped_to_the_canvas_design(self):
        assert re.search(
            r'^\s+\.hx-form-field\[data-hx-label-position="left"\],$',
            FORM_FIELD_CSS,
            re.MULTILINE,
        )

    def test_compact_single_column_only_without_a_label_position(self):
        rule = next(
            line
            for line in DATA_FORM_CSS.splitlines()
            if "grid-template-columns" not in line and ".hx-data-form:not(" in line
        )

        assert "[data-hx-label-position] .hx-data-form" in rule
        assert ":has(> .hx-data-form__cell)" in rule

    def test_drawer_footer_in_both_designs(self):
        assert "\n.hx-data-form-drawer {" in DATA_FORM_CSS
        assert (
            "\n.hx-drawer > aside > section:has(> .hx-data-form-drawer) {"
            in DATA_FORM_CSS
        )

    def test_no_page_scroll_behind_an_open_drawer(self):
        assert "html:has(.hx-drawer > aside > section > *) {" in DRAWER_CSS
        assert "overscroll-behavior: contain;" in DRAWER_CSS
        assert "overscroll-behavior: contain;" in DATA_FORM_CSS
