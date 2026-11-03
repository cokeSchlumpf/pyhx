"""Only for the demo of a dropped connection on the job page.

"Drop the connection" ends the job's event response without ``pyhx-close``,
as a proxy timeout or a restart of the app would. The browser then reconnects
by itself and sends the id of the last event it received (``Last-Event-ID``).
"""

import htpy as y
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pyhx.core import WebAppRouter

router = WebAppRouter()

_DROP: set[str] = set()
"""Ids of the jobs whose event response is ended at its next chunk."""


class _Dropped(Exception):
    pass


class DropConnections:
    """ASGI middleware ending the event response of a job in ``_DROP``."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        parts = scope.get("path", "").split("/")  # /jobs/<id>/events
        if scope["type"] != "http" or parts[1:2] != ["jobs"] or parts[3:] != ["events"]:
            await self.app(scope, receive, send)
            return

        async def dropping_send(message: Message) -> None:
            if parts[2] in _DROP and message["type"] == "http.response.body":
                _DROP.discard(parts[2])
                await send({"type": "http.response.body", "body": b""})
                raise _Dropped()
            await send(message)

        try:
            await self.app(scope, receive, dropping_send)
        except _Dropped:
            pass


@router.fragment.post("/jobs/{job_id}/drop")
async def drop_connection(job_id: str) -> y.Node:
    _DROP.add(job_id)
    return ""
