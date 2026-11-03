from typing import Protocol, runtime_checkable

from fastapi import Response


@runtime_checkable
class HandlerResponse(Protocol):
    def to_response(self) -> Response: ...
