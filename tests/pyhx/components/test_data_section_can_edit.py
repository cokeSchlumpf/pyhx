"""``can_edit`` resolution: permission gate plus optional custom edit renderer."""

import asyncio

import htpy as y
from pydantic import BaseModel

from pyhx.components.data.data_section import DataSection
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core.fragment import FragmentFactory, FragmentResponse
from pyhx.core.page import PageDecoratorFactory


class Person(BaseModel):
    id: int
    name: str


ANN = Person(id=1, name="Ann")


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


def _section(**kwargs) -> DataSection:
    return DataSection(
        routes=_Routes(),
        name="people",
        path="/people",
        source=SimpleDataSource([ANN]),
        type=Person,
        **kwargs,
    )


async def _render(node: y.Node) -> str:
    """Render a node the way ``HtpyResponse`` does.

    The section hands back node trees with un-awaited coroutines embedded in
    them (``render_drawer``, ``table.render``); ``aiter_chunks`` is what
    resolves them, so a test that only inspects the return value would leave
    those coroutines dangling.
    """
    return "".join(
        [
            chunk.decode() if isinstance(chunk, bytes) else chunk
            async for chunk in y.fragment[node].aiter_chunks()
        ]
    )


def _resolve(**kwargs):
    return asyncio.run(_section(**kwargs)._resolve_can_edit())


def _select(**kwargs):
    """Run an edit click, for the paths that return early without a node."""
    return asyncio.run(_section(**kwargs)._on_select([ANN]))


def _select_html(**kwargs) -> str:
    async def run() -> str:
        return await _render(await _section(**kwargs)._on_select([ANN]))

    return asyncio.run(run())


class TestResolution:
    def test_defaults_to_editable(self):
        assert _resolve() is True

    def test_false_is_not_editable(self):
        assert _resolve(can_edit=False) is False

    def test_producer_is_called_with_no_arguments(self):
        assert _resolve(can_edit=lambda: False) is False

    def test_async_producer_is_awaited(self):
        async def can_edit() -> bool:
            return False

        assert _resolve(can_edit=can_edit) is False

    def test_item_renderer_is_returned_uncalled(self):
        # Arity is what distinguishes the renderer from a 0-arg producer:
        # resolve_value would otherwise call it with no arguments.
        resolved = _resolve(can_edit=lambda item: FragmentResponse.redirect("/x"))

        assert callable(resolved)

    def test_producer_may_return_an_item_renderer(self):
        renderer = lambda item: FragmentResponse.redirect("/x")

        assert callable(_resolve(can_edit=lambda: renderer))

    def test_renderer_needs_a_required_positional_parameter(self):
        # Documented constraint. A defaulted parameter leaves no *required*
        # positional, so the renderer reads as a 0-arg producer: it gets
        # called with no item and its FragmentResponse is taken for a bool.
        def render(item=None) -> FragmentResponse:
            return FragmentResponse.redirect("/x")

        assert _resolve(can_edit=render) is True


class TestEditClick:
    def test_not_editable_renders_nothing(self):
        assert _select(can_edit=False) is None

    def test_editable_renders_the_built_in_drawer(self):
        assert "<form" in _select_html()

    def test_renderer_receives_the_clicked_item(self):
        seen: list[Person] = []

        def render(item: Person) -> FragmentResponse:
            seen.append(item)
            return FragmentResponse.redirect(f"/people/{item.id}")

        result = _select(can_edit=render)

        assert seen == [ANN]
        assert isinstance(result, FragmentResponse)
        assert result.headers == {"HX-Redirect": "/people/1"}

    def test_async_renderer_is_awaited(self):
        async def render(item: Person) -> FragmentResponse:
            return FragmentResponse.redirect(f"/people/{item.id}")

        result = _select(can_edit=render)

        assert isinstance(result, FragmentResponse)
        assert result.headers == {"HX-Redirect": "/people/1"}


class TestSubmitGuard:
    def test_renderer_permits_the_update_without_being_called(self):
        # The guard only needs a yes/no, so invoking a renderer that might
        # query or log would be a spurious side effect.
        calls: list[Person] = []

        def render(item: Person) -> FragmentResponse:
            calls.append(item)
            return FragmentResponse.redirect("/x")

        async def run() -> None:
            section = _section(can_edit=render)
            await _render(await section._on_edit_form_submit(Person(id=1, name="Bob")))
            assert await section.source.get_by_id("1") == Person(id=1, name="Bob")

        asyncio.run(run())

        assert calls == []

    def test_not_editable_refuses_the_update(self):
        async def run() -> None:
            section = _section(can_edit=False)
            assert await section._on_edit_form_submit(Person(id=1, name="Bob")) is None
            assert (await section.source.get_by_id("1")).name == "Ann"

        asyncio.run(run())
