"""Typed, read-only access to the WebApp's app-level context dict.

:class:`AppContext` wraps the mutable ``dict[str, Any]`` owned by
:class:`~pyhx.core.webapp.WebApp` and exposes:

* a read-only :attr:`AppContext.values` mapping view, and
* a typed :meth:`AppContext.get` lookup with two call shapes — by key
  + expected type, or by type alone (uniqueness-required).

The wrapper holds the dict **by reference**, so mutations made on the
WebApp via :meth:`~pyhx.core.webapp.WebApp.set_context` are visible to
existing :class:`AppContext` instances immediately. This lets the same
:class:`AppContext` be shared by the WebApp and by every per-request
:class:`~pyhx.core.request_context.RequestContext` without snapshotting
on each request.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, overload


class AppContext:
    """Read-side view of the WebApp's app-level context."""

    def __init__(self, source: dict[str, Any]) -> None:
        """Wrap ``source`` by reference.

        Mutations to ``source`` after construction are reflected by
        :attr:`values` and :meth:`get`. The wrapper itself exposes no
        mutation API — writes go through the WebApp.
        """
        self._source = source

    @property
    def values(self) -> Mapping[str, Any]:
        """Read-only mapping view of the underlying context dict.

        Backed by :class:`types.MappingProxyType`, so attempted writes
        raise :class:`TypeError` at the proxy. Iteration and lookups
        see the latest WebApp state because the proxy wraps the same
        dict object.
        """
        return MappingProxyType(self._source)

    @overload
    def get[T](self, key: str, type: type[T], /) -> T: ...
    @overload
    def get[T](self, type: type[T], /) -> T: ...

    def get(self, key_or_type: str | type, target_type: type | None = None) -> Any:
        """Typed lookup against the context dict.

        Two call shapes, dispatched at runtime on ``key_or_type``'s
        runtime type:

        * ``get(key, type)`` — look up by key, then ``isinstance`` the
          value against ``type``. Raises :class:`KeyError` if the key
          is absent; raises :class:`TypeError` if the stored value is
          of the wrong type.
        * ``get(type)`` — scan all values for entries that are
          instances of ``type``. Returns the single match. Raises
          :class:`LookupError` if zero or more than one entry matches.

        ``isinstance`` is used rather than exact ``type() is …`` so a
        subclass entry satisfies a parent-class lookup.
        """
        if isinstance(key_or_type, str):
            key = key_or_type
            if key not in self._source:
                raise KeyError(
                    f"AppContext: no entry for key {key!r} "
                    f"(have keys: {sorted(self._source)!r})"
                )
            value = self._source[key]
            if target_type is not None and not isinstance(value, target_type):
                raise TypeError(
                    f"AppContext[{key!r}]: expected {target_type.__name__}, "
                    f"got {value.__class__.__name__}"
                )
            return value

        scan_type = key_or_type
        matches = [v for v in self._source.values() if isinstance(v, scan_type)]
        if not matches:
            raise LookupError(f"AppContext: no entry of type {scan_type.__name__}")
        if len(matches) > 1:
            raise LookupError(
                f"AppContext: {len(matches)} entries of type "
                f"{scan_type.__name__} — expected exactly one"
            )
        return matches[0]
