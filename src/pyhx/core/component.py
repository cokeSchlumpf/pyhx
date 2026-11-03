import functools
import inspect
from collections.abc import Awaitable, Callable
from http import HTTPMethod
from typing import ParamSpec, Protocol, overload

import htpy as y

from .fragment import (
    Fragment,
    FragmentDefinition,
    FragmentResult,
    resolve_fragment_result,
)
from .fragment_registry import get_fragment_registry
from .primitives import PathTemplate
from .stream import DEFAULT_KEEPALIVE, Stream, StreamDefinition, StreamFn

P = ParamSpec("P")


class ComponentFragmentFactory:
    def __init__(
        self,
        fragments: list[Fragment],
        on_register: Callable[[Fragment], None] | None = None,
    ) -> None:
        self._fragments = fragments
        self._on_register = on_register

    def _add(
        self, path: str, method: HTTPMethod
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        def __call__(fn: Callable[..., Awaitable[FragmentResult]]) -> Fragment:
            fragment = FragmentDefinition(
                self._path(fn, path), method, resolve_fragment_result(fn)
            )
            self._register(fragment)
            return fragment

        return __call__

    @staticmethod
    def _path(fn: Callable[..., object], path: str) -> PathTemplate:
        return PathTemplate(f"/_components/{fn.__name__}").join(PathTemplate(path))

    def _register(self, fragment: Fragment) -> None:
        self._fragments.append(fragment)
        if self._on_register is not None:
            self._on_register(fragment)

    def delete(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._add(path, HTTPMethod.DELETE)

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._add(path, HTTPMethod.GET)

    def patch(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._add(path, HTTPMethod.PATCH)

    def post(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._add(path, HTTPMethod.POST)

    def put(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._add(path, HTTPMethod.PUT)

    def stream(
        self, path: str, *, keepalive: float | None = DEFAULT_KEEPALIVE
    ) -> Callable[[StreamFn], Stream]:
        """Register a server-sent event stream, see :meth:`StreamFactory.get`."""

        def __call__(fn: StreamFn) -> Stream:
            stream = StreamDefinition(self._path(fn, path), fn, keepalive=keepalive)
            self._register(stream)
            return stream

        return __call__


class Component[**P](Protocol):
    fragments: ComponentFragmentFactory
    fn: Callable[P, y.Node]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> y.Node: ...


@overload
def component(fn: Callable[P, y.Node]) -> Component[P]: ...


@overload
def component(
    *,
    auto_register: bool = True,
) -> Callable[[Callable[P, y.Node]], Component[P]]: ...


def component(
    fn: Callable[P, y.Node] | None = None,
    *,
    auto_register: bool = True,
) -> Component[P] | Callable[[Callable[P, y.Node]], Component[P]]:
    def _decorate(fn: Callable[P, y.Node]) -> Component[P]:
        on_register = get_fragment_registry().register if auto_register else None

        class ComponentImpl:
            fragments: ComponentFragmentFactory

            def __init__(self) -> None:
                self.fn = fn
                self._fragments: list[Fragment] = []
                self.fragments = ComponentFragmentFactory(self._fragments, on_register)

            def __call__(self, *args: P.args, **kwargs: P.kwargs) -> y.Node:
                return self.fn(*args, **kwargs)

        ComponentImpl.__call__.__signature__ = inspect.signature(fn)  # type: ignore[attr-defined]
        ComponentImpl.__call__.__annotations__ = dict(fn.__annotations__)

        instance = ComponentImpl()
        functools.update_wrapper(instance, fn, updated=())

        return instance

    if fn is None:
        return _decorate
    return _decorate(fn)
