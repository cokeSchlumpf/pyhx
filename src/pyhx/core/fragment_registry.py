from collections.abc import Awaitable, Callable
from http import HTTPMethod

from .fragment import (
    Fragment,
    FragmentDefinition,
    FragmentResult,
    resolve_fragment_result,
)
from .log import LOG
from .primitives import PathTemplate

FragmentListener = Callable[[Fragment], None]


class FragmentRegistry:
    """Process-global registry that collects fragments declared before any
    WebApp exists.

    Components register fragments here at module-import time (via the
    ``@component`` decorator). A WebApp, once constructed, attaches via
    :meth:`subscribe` to replay existing fragments and receive future ones.

    Notes
    -----
    - Not thread-safe; intended for single-threaded import + app startup.
    - Replay order equals registration (insertion) order.
    - Listeners MUST NOT call :meth:`register` synchronously from within
      their callback (would mutate ``_fragments`` mid-iteration).
    """

    def __init__(self) -> None:
        self._fragments: list[Fragment] = []
        self._listeners: list[FragmentListener] = []

    def register(self, fragment: Fragment) -> None:
        """Append ``fragment`` and notify every current listener."""
        self._fragments.append(fragment)
        LOG.debug(
            "FragmentRegistry: registered %s %s",
            fragment.method,
            fragment.path,
        )
        for listener in list(self._listeners):
            listener(fragment)

    def subscribe(
        self,
        listener: FragmentListener,
        *,
        replay: bool = True,
    ) -> Callable[[], None]:
        """Attach ``listener``. Returns an unsubscribe callable.

        When ``replay`` is True (default), the listener is invoked once per
        already-registered fragment, in insertion order, before being added
        to the live listener list.
        """
        if replay:
            for fragment in self._fragments:
                listener(fragment)
        self._listeners.append(listener)

        def _unsubscribe() -> None:
            try:
                self._listeners.remove(listener)
            except ValueError:
                pass

        return _unsubscribe

    def fragments(self) -> tuple[Fragment, ...]:
        """Immutable snapshot of currently registered fragments."""
        return tuple(self._fragments)

    def clear(self) -> None:
        """Reset all state. **Test-only.** Drops fragments AND listeners."""
        self._fragments.clear()
        self._listeners.clear()


_registry = FragmentRegistry()


def get_fragment_registry() -> FragmentRegistry:
    """Return the process-global :class:`FragmentRegistry` singleton."""
    return _registry


class RegistryFragmentFactory:
    """Fragment factory that registers fragments through the global
    :class:`FragmentRegistry` instead of a specific :class:`WebApp`.

    Use this when declaring fragments at module-import time (e.g. via
    ``@hx.fragment.get(...)``): the registration survives even if no
    ``WebApp`` exists yet, and is replayed once one is constructed.
    """

    def _create(
        self, path: str, method: HTTPMethod
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        def __call__(fn: Callable[..., Awaitable[FragmentResult]]) -> Fragment:
            fragment = FragmentDefinition(
                PathTemplate(path), method, resolve_fragment_result(fn)
            )
            get_fragment_registry().register(fragment)
            return fragment

        return __call__

    def delete(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.DELETE)

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.GET)

    def patch(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.PATCH)

    def post(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.POST)

    def put(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.PUT)
