from typing import Generic, TypeVar

from pydantic import BaseModel

from pyhx.core.primitives.resolve_value import SyncOrAsyncFn, resolve_async_fn

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M", bound=BaseModel)


class ModelType(Generic[T, M]):
    """Pairs a target type with bi-directional mapping functions.

    ``map_to`` / ``map_from`` may each be either sync or async at
    construction. Sync callables are wrapped into coroutine functions
    immediately, so the stored attributes are always awaitable and
    callers can treat the pair uniformly.
    """

    def __init__(
        self,
        type: type[M],
        map_to: SyncOrAsyncFn[T, M],
        map_from: SyncOrAsyncFn[M, T],
    ) -> None:
        self.type = type
        self.map_to = resolve_async_fn(map_to)
        self.map_from = resolve_async_fn(map_from)

    @staticmethod
    def from_models[A: BaseModel, B: BaseModel](
        source_type: type[A],
        target_type: type[B],
    ) -> "ModelType[A, B]":
        """Build a ``ModelType`` that round-trips two Pydantic models.

        Both directions go through ``model_dump`` → ``model_validate``:
        a structural copy that drops fields absent on the receiving
        schema and applies its defaults / validators. Suitable when ``A``
        and ``B`` share enough fields that a plain re-validation suffices
        (e.g. a domain model and its edit-form view of the same data).
        For non-trivial transformations, build the ``ModelType`` directly
        with custom ``map_to`` / ``map_from`` callables instead.

        Trailing underscore in the name avoids the ``from`` keyword.
        """

        def to_target(item: A) -> B:
            return target_type.model_validate(item.model_dump())

        def from_target(item: B) -> A:
            return source_type.model_validate(item.model_dump())

        return ModelType(target_type, to_target, from_target)
