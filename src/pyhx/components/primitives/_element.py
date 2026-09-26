from collections.abc import Mapping

import htpy as y

from pyhx.core.primitives import classnames as cx


class _HxElement:
    """Deferred-render protocol: ``obj[children]`` and ``str(obj)`` both render.

    Subclasses populate their state in ``__init__`` and implement ``_render``.
    """

    _children: y.Node = None

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        self._children = children
        return self._render()

    def __html__(self) -> str:
        return str(self._render())

    def _render(self) -> y.Node:
        raise NotImplementedError


class _KxSimpleElement(_HxElement):
    """A styled element wrapper: fixed tag + BEM class, pass-through attrs/children."""

    def __init__(
        self,
        class_name: str,
        element: y.Element = y.div,
        children: y.Node = None,
        *args: Mapping[str, y.Attribute],
        **kwargs: y.Attribute,
    ) -> None:
        self._class_name = class_name
        self._element = element
        self._children = children
        self._args = args
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return self._element(*self._args, **cx(self._class_name, **self._kwargs))[
            self._children
        ]


class _KxSimpleElementFactory:
    """Creates fresh :class:`_KxSimpleElement` instances so children never leak between renders."""

    def __init__(self, class_name: str, element: y.Element = y.div) -> None:
        self._class_name = class_name
        self._element = element

    def __call__(
        self, *args: Mapping[str, y.Attribute], **kwargs: y.Attribute
    ) -> _KxSimpleElement:
        return _KxSimpleElement(self._class_name, self._element, None, *args, **kwargs)

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]
