import asyncio

import htpy as y
from pydantic import BaseModel, Field
from starlette.datastructures import FormData

from pyhx.components.data import FormRenderContext, HeadlessForm


# ----------------------------------------------------------------------------
# Test fixtures
# ----------------------------------------------------------------------------


class _Model(BaseModel):
    title: str = Field(min_length=3)
    tags: list[str] = Field(default_factory=list)
    active: bool = False


class _Fragment:
    def url(self, **kwargs) -> str:
        return "/_components/headless-form/test/x"


class _FragmentFactory:
    def __init__(self) -> None:
        self.registered: list[tuple[str, str]] = []

    def add(self, path, method, fn) -> _Fragment:
        self.registered.append((path, method))
        return _Fragment()


class _Routes:
    def __init__(self) -> None:
        self.fragment = _FragmentFactory()


class _Request:
    """Minimal stand-in exposing the async ``form()`` the parser awaits."""

    def __init__(self, items: list[tuple[str, str]]) -> None:
        self._form = FormData(items)

    async def form(self) -> FormData:
        return self._form


def _make_form(routes: _Routes | None = None, **kwargs) -> HeadlessForm[_Model]:
    async def _render(ctx: FormRenderContext[_Model]) -> y.Node:
        return y.div["rendered"]

    async def _submit(value: _Model):
        return y.div["saved"]

    return HeadlessForm[_Model](
        routes=routes or _Routes(),
        name="Test Form",
        type=_Model,
        render=_render,
        handle_submit=_submit,
        **kwargs,
    )


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


class TestConstruction:
    def test_name_is_kebab_cased(self) -> None:
        form = _make_form()
        assert form.name == "test-form"
        assert form.wrapper_div_id == "hx-headless-form__test-form"

    def test_registers_submit_and_validate_fragments(self) -> None:
        routes = _Routes()
        _make_form(routes)
        paths = {p for p, _ in routes.fragment.registered}
        assert "/_components/headless-form/test-form/submit" in paths
        assert "/_components/headless-form/test-form/validate" in paths


class TestDeriveListFields:
    def test_only_list_typed_fields(self) -> None:
        form = _make_form()
        assert form._list_fields == {"tags"}

    def test_override_wins(self) -> None:
        form = _make_form(list_fields={"title"})
        assert form._list_fields == {"title"}


class TestParseForm:
    def test_list_field_collects_repeated_keys(self) -> None:
        form = _make_form()
        req = _Request([("title", "hello"), ("tags", "a"), ("tags", "b")])
        parsed = asyncio.run(form._parse_form(req))  # type: ignore[arg-type]
        assert parsed == {"title": "hello", "tags": ["a", "b"], "active": False}

    def test_bool_uses_key_presence(self) -> None:
        form = _make_form()
        present = asyncio.run(
            form._parse_form(_Request([("title", "hello"), ("active", "on")]))  # type: ignore[arg-type]
        )
        assert present["active"] is True
        absent = asyncio.run(form._parse_form(_Request([("title", "hello")])))  # type: ignore[arg-type]
        assert absent["active"] is False

    def test_empty_string_scalar_becomes_none(self) -> None:
        form = _make_form()
        parsed = asyncio.run(form._parse_form(_Request([("title", "")])))  # type: ignore[arg-type]
        assert parsed["title"] is None


class TestParseTouched:
    def test_keeps_only_known_fields(self) -> None:
        form = _make_form()
        req = _Request([("_touched", "title"), ("_touched", "bogus")])
        touched = asyncio.run(form._parse_touched(req))  # type: ignore[arg-type]
        assert touched == {"title"}


class TestValidationErrorsToDict:
    def test_first_message_per_field(self) -> None:
        form = _make_form()
        try:
            _Model.model_validate({"title": "ab"})
        except Exception as exc:  # pydantic.ValidationError
            errors = form._validation_errors_to_dict(exc)  # type: ignore[arg-type]
        assert "title" in errors


class TestRender:
    def test_visible_errors_filtered_by_touched(self) -> None:
        captured: dict = {}

        async def _render(ctx: FormRenderContext[_Model]) -> y.Node:
            captured["ctx"] = ctx
            return y.div

        form = HeadlessForm[_Model](
            routes=_Routes(),
            name="t",
            type=_Model,
            render=_render,
            handle_submit=lambda v: y.div,  # type: ignore[arg-type]
        )

        asyncio.run(
            form.render(
                value=_Model.model_construct(title="ab"),
                errors={"title": "too short"},
                touched=set(),
            )
        )
        ctx = captured["ctx"]
        # Full error set is visible to the layout (drives submit gating)...
        assert ctx.errors == {"title": "too short"}
        # ...but no errors are *displayed* until the field is touched.
        assert ctx.visible_errors == {}

        asyncio.run(
            form.render(
                value=_Model.model_construct(title="ab"),
                errors={"title": "too short"},
                touched={"title"},
            )
        )
        assert captured["ctx"].visible_errors == {"title": "too short"}

    def test_initial_render_revalidates_when_errors_none(self) -> None:
        captured: dict = {}

        async def _render(ctx: FormRenderContext[_Model]) -> y.Node:
            captured["ctx"] = ctx
            return y.div

        form = HeadlessForm[_Model](
            routes=_Routes(),
            name="t",
            type=_Model,
            render=_render,
            handle_submit=lambda v: y.div,  # type: ignore[arg-type]
        )

        # title too short → re-validation populates errors even though the
        # caller passed errors=None.
        asyncio.run(form.render(value=_Model.model_construct(title="ab")))
        assert "title" in captured["ctx"].errors
