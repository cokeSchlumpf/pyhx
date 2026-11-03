# T-017 End streams at shutdown

## Problem

A stream that stays open for as long as a page is shown (e.g. the live changes of a record, not a job that ends) keeps a connection open. Servers like uvicorn wait for open responses before they stop and tell them nothing about the shutdown, so a reload of `fastapi dev` serves nothing until every such page is closed, and a deployment waits for its graceful-shutdown timeout. pyhx streams can't know that the process is stopping.

## Proposed outcome

- When the process is asked to stop (`SIGTERM`, `SIGINT`), every open stream ends its response without `pyhx-close`, so the server stops at once and the browser reconnects to the next process.
- A stream that starts after that ends at once too.
- A function `end_streams()` does the same for servers that stop in another way, and for tests.
- Streams that end by themselves still send `pyhx-close`; nothing else changes.

## Affected users and systems

- **Apps with streams:** reloads and deployments no longer wait for open streams. First user: app--casesight T-020 (one stream per open case page).

## Constraints

- Non-breaking, released as a minor version on `versions/1`.
- Works with uvicorn as `fastapi dev` and `fastapi run` start it; doesn't change what the server does on the signal.

## Open questions

None.
