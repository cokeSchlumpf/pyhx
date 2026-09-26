from typing import Protocol

from fastapi import Response


class HandlerResponse(Protocol):
    def to_response(self) -> Response: ...
