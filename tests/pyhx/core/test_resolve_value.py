import asyncio

import htpy as y
import pytest

from pyhx.core.primitives import resolve_value


class TestResolveValue:
    def test_plain_value_passes_through(self):
        assert asyncio.run(resolve_value("text")) == "text"

    def test_sync_producer_is_called(self):
        assert asyncio.run(resolve_value(lambda: "text")) == "text"

    def test_async_producer_is_awaited(self):
        async def produce() -> str:
            return "text"

        assert asyncio.run(resolve_value(produce)) == "text"

    @pytest.mark.parametrize(
        "node",
        [
            y.span(class_="org")["SVA Zürich"],  # Element with attributes
            y.input(type="text", name="q"),  # VoidElement, not an Element subclass
            y.div,  # bare element
        ],
    )
    def test_htpy_element_is_not_called(self, node):
        resolved = asyncio.run(resolve_value(node))

        assert resolved is node
        assert str(resolved) == str(node)

    def test_producer_of_htpy_element_is_called(self):
        resolved = asyncio.run(resolve_value(lambda: y.span(class_="org")["SVA"]))

        assert str(resolved) == '<span class="org">SVA</span>'

    def test_fragment_passes_through(self):
        node = y.fragment["a", y.b(class_="x")["b"]]

        assert asyncio.run(resolve_value(node)) is node
