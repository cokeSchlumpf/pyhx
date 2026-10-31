# T-001 Core API with private state

## Problem

The PyHX Core API is the foundational wrapper around FastAPI to enable simple, declarative configuration of web applications, HTMX fragments and websockets. Its internal state should not be changeable from outside except through its public functions.

## Proposed outcome

- Internal properties are really private: they are only returned as immutable objects, and modifications are only possible via public functions.
