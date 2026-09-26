# Installation

## Requirements

- Python **3.12** or newer
- An ASGI server such as [uvicorn](https://www.uvicorn.org/) (any FastAPI-compatible server works)

## Install

With Poetry:

```bash
poetry add pyhx
```

With pip:

```bash
pip install pyhx
```

That pulls in PyHX itself along with its required runtime dependencies (FastAPI, htpy, python-multipart).

## Verify

Drop the following into `app.py`:

```python
import htpy as y
from pyhx.core import WebApp

app = WebApp(title="Smoke Test")

@app.page("/", title="Home")
async def home() -> y.Node:
    return y.h1["It works."]

fastapi_app = app.create_app()
```

Then run:

```bash
uvicorn app:fastapi_app --reload
```

Open `http://127.0.0.1:8000/` — you should see "It works.".

When that's green, head over to [Your First App](first-app.md) for a slightly more interesting walk-through.
