"""Normalise sync-or-async value producers and functions into async ones.

Two pairs of helpers, both about the same underlying problem: callers
want to accept either a sync or an async callable without forcing every
receiving code path to spell out the branches.

* :data:`SyncOrAsyncValue` / :func:`resolve_value` — 0-arg producers (or
  bare values). Returns the **resolved value** immediately.
* :data:`SyncOrAsyncFn` / :func:`resolve_async_fn` — 1-arg functions.
  Returns an **always-async wrapped callable**, so the caller can store
  it once and ``await`` it many times.

The asymmetry is deliberate: resolving a 0-arg value happens once at
the boundary; wrapping a function happens once at construction so every
later call site is a uniform ``await fn(x)``.
"""

from collections.abc import Awaitable, Callable
from inspect import iscoroutinefunction
from typing import cast

type SyncOrAsyncValue[C] = Callable[[], C] | Callable[[], Awaitable[C]] | C
"""A value, a sync producer of one, or an async producer of one.

Pair with :func:`resolve_value`. Note the inherent ambiguity: if ``C``
itself is callable (e.g. you want to resolve to a function), this type
can't distinguish a producer from the value it produces. Don't use it
when ``C`` may be callable.
"""


type SyncOrAsyncFn[A, B] = Callable[[A], B] | Callable[[A], Awaitable[B]]
"""A 1-arg function, either sync or async.

Pair with :func:`resolve_async_fn`.
"""


async def resolve_value[C](value: SyncOrAsyncValue[C]) -> C:
    """Materialize a :data:`SyncOrAsyncValue` into a concrete ``C``.

    Plain values pass through unchanged. Sync callables are invoked;
    async callables are invoked and awaited. The result is always a
    fully-resolved ``C``.
    """
    if callable(value):
        if iscoroutinefunction(value):
            return await value()
        result = value()
        if isinstance(result, Awaitable):
            return await result
        return cast(C, result)
    return value


def resolve_async_fn[A, B](
    fn: SyncOrAsyncFn[A, B],
) -> Callable[[A], Awaitable[B]]:
    """Coerce ``fn`` to an always-async callable, wrapping sync funcs as needed.

    Unlike :func:`resolve_value`, this **does not call** ``fn`` — it
    returns a wrapped callable that defers execution until the caller
    awaits it. Useful when the wrapped function will be invoked many
    times (e.g. stored on a long-lived object) so the wrapping cost is
    paid once instead of per call.
    """
    if iscoroutinefunction(fn):
        return cast(Callable[[A], Awaitable[B]], fn)

    sync_fn = cast(Callable[[A], B], fn)

    async def wrapper(arg: A) -> B:
        return sync_fn(arg)

    return wrapper
