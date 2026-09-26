"""DataForm grid layout: row spans + field-keyed ``template_areas``."""

import asyncio

import htpy as y
from pydantic import BaseModel
from typing import Annotated

from pyhx.components import annotations as a
from pyhx.components.data.data_form import DataForm, _span_class


# ----------------------------------------------------------------------------
# Routes stub (mirrors tests/pyhx/components/test_headless_form.py)
# ----------------------------------------------------------------------------


class _Fragment:
    def url(self, **kwargs) -> str:
        return "/x"


class _FragmentFactory:
    def add(self, path, method, fn) -> _Fragment:
        return _Fragment()


class _Routes:
    def __init__(self) -> None:
        self.fragment = _FragmentFactory()


def _form(model: type) -> DataForm:
    return DataForm(routes=_Routes(), name="t", type=model, handle_submit=_noop)  # type: ignore[arg-type]


async def _noop(value):  # pragma: no cover - never invoked in these tests
    return y.div


def _html(form: DataForm) -> str:
    return str(asyncio.run(form.render()))


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@a.form(columns=2)
class _SpanModel(BaseModel):
    bio: Annotated[str, a.TextField(columns=2, rows=2)]
    nickname: Annotated[str, a.TextField()]


@a.form(
    template_areas=["title title", "summary author"],
    template_columns=["2fr", "1fr"],
)
class _TemplateModel(BaseModel):
    title: Annotated[str, a.TextField()]
    summary: Annotated[str, a.TextField()]
    author: Annotated[str, a.TextField()]
    secret: Annotated[str, a.HiddenField()] = "x"


# ----------------------------------------------------------------------------
# _span_class
# ----------------------------------------------------------------------------


class TestSpanClass:
    def test_none_when_unset(self) -> None:
        assert _span_class(a.TextField()) == ""

    def test_column_span_only(self) -> None:
        assert _span_class(a.TextField(columns=3)) == "hx-grid-span-3"

    def test_row_span_only(self) -> None:
        assert _span_class(a.TextField(rows=2)) == "hx-grid-row-span-2"

    def test_both_spans(self) -> None:
        cls = _span_class(a.TextField(columns=2, rows=2))
        assert "hx-grid-span-2" in cls
        assert "hx-grid-row-span-2" in cls


# ----------------------------------------------------------------------------
# _grid_style
# ----------------------------------------------------------------------------


class TestGridStyle:
    def test_default_uses_column_count(self) -> None:
        @a.form(columns=3)
        class _M(BaseModel):
            a: Annotated[str, a.TextField()]

        assert _form(_M)._grid_style() == "--hx-grid-columns: 3"

    def test_template_columns_emits_track_sizes(self) -> None:
        style = _form(_TemplateModel)._grid_style()
        assert "grid-template-columns: 2fr 1fr" in style
        # explicit tracks supersede the --hx-grid-columns custom property
        assert "--hx-grid-columns" not in style

    def test_template_areas_quoted_rows(self) -> None:
        style = _form(_TemplateModel)._grid_style()
        assert "grid-template-areas: 'title title' 'summary author'" in style

    def test_template_areas_derives_columns_without_explicit_widths(self) -> None:
        @a.form(template_areas=["a b c", "a b c"])
        class _M(BaseModel):
            a: Annotated[str, a.TextField()]
            b: Annotated[str, a.TextField()]
            c: Annotated[str, a.TextField()]

        assert "--hx-grid-columns: 3" in _form(_M)._grid_style()

    def test_template_rows(self) -> None:
        @a.form(template_rows=["auto", "1fr"])
        class _M(BaseModel):
            a: Annotated[str, a.TextField()]

        assert "grid-template-rows: auto 1fr" in _form(_M)._grid_style()


# ----------------------------------------------------------------------------
# Rendered HTML
# ----------------------------------------------------------------------------


class TestRenderedHtml:
    def test_row_span_class_present(self) -> None:
        html = _html(_form(_SpanModel))
        assert "hx-grid-row-span-2" in html
        assert "hx-grid-span-2" in html

    def test_template_grid_styles_present(self) -> None:
        html = _html(_form(_TemplateModel))
        assert "grid-template-columns: 2fr 1fr" in html
        # htpy HTML-escapes the quote chars in the attribute (browser decodes
        # them back before CSS parsing), so assert on the unquoted row content.
        assert "grid-template-areas:" in html
        assert "title title" in html
        assert "summary author" in html

    def test_visible_fields_get_grid_area(self) -> None:
        html = _html(_form(_TemplateModel))
        for field in ("title", "summary", "author"):
            assert f"grid-area: {field}" in html

    def test_hidden_field_gets_no_grid_area(self) -> None:
        html = _html(_form(_TemplateModel))
        assert "grid-area: secret" not in html


# ----------------------------------------------------------------------------
# _place_field
# ----------------------------------------------------------------------------


class TestPlaceField:
    def test_passthrough_without_template(self) -> None:
        form = _form(_SpanModel)
        node = y.div["x"]
        assert form._place_field("bio", node) is node

    def test_none_passthrough(self) -> None:
        form = _form(_TemplateModel)
        assert form._place_field("title", None) is None

    def test_wraps_visible_field_in_template_mode(self) -> None:
        form = _form(_TemplateModel)
        wrapped = form._place_field("title", y.div["x"])
        assert "grid-area: title" in str(wrapped)

    def test_hidden_field_not_wrapped(self) -> None:
        form = _form(_TemplateModel)
        node = y.input(type="hidden", name="secret")
        assert form._place_field("secret", node) is node


# ----------------------------------------------------------------------------
# IgnoreField
# ----------------------------------------------------------------------------


class _IgnoreModel(BaseModel):
    internal_id: Annotated[str, a.IgnoreField()]
    name: Annotated[str, a.TextField()]


def test_ignore_field_absent_from_form_fields():
    form = _form(_IgnoreModel)
    assert "internal_id" not in form.form_fields
    assert "name" in form.form_fields


def test_ignore_field_renders_no_markup():
    html = _html(_form(_IgnoreModel))
    assert 'name="internal_id"' not in html
    assert 'name="name"' in html


# ----------------------------------------------------------------------------
# Hidden-field auto-include
# ----------------------------------------------------------------------------


class _HiddenOrderModel(BaseModel):
    record_id: Annotated[str, a.HiddenField()]
    title: Annotated[str, a.TextField()]
    subtitle: Annotated[str, a.TextField()]


def test_hidden_field_autoincluded_when_omitted_from_field_order():
    form = DataForm(
        routes=_Routes(),  # type: ignore[arg-type]
        name="t",
        type=_HiddenOrderModel,
        handle_submit=_noop,
        field_order=["title", "subtitle"],
    )
    # record_id is not in field_order but is hidden -> kept, appended last.
    assert list(form.form_fields) == ["title", "subtitle", "record_id"]
    html = _html(form)
    assert 'type="hidden"' in html and 'name="record_id"' in html


def test_hidden_field_keeps_named_position_when_in_field_order():
    form = DataForm(
        routes=_Routes(),  # type: ignore[arg-type]
        name="t",
        type=_HiddenOrderModel,
        handle_submit=_noop,
        field_order=["record_id", "title", "subtitle"],
    )
    assert list(form.form_fields) == ["record_id", "title", "subtitle"]


class _IgnoreOrderModel(BaseModel):
    internal_id: Annotated[str, a.IgnoreField()]
    title: Annotated[str, a.TextField()]


def test_ignore_field_overrides_explicit_field_order():
    form = DataForm(
        routes=_Routes(),  # type: ignore[arg-type]
        name="t",
        type=_IgnoreOrderModel,
        handle_submit=_noop,
        field_order=["internal_id", "title"],
    )
    assert "internal_id" not in form.form_fields
    assert list(form.form_fields) == ["title"]
