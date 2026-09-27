# Installation

## Requirements

- Python **3.12** or newer
- An ASGI server such as [uvicorn](https://www.uvicorn.org/) (any FastAPI-compatible server works)

## Install

PyHX is installed directly from GitHub. Pin it to a release tag (e.g. `v0.2.0`) or follow a major version with its
branch (e.g. `versions/0`, always the latest `0.x` release). All releases are listed in the
[changelog](../changelog.md).

=== "Poetry"

    ```bash
    # exact release
    poetry add "git+https://github.com/cokeSchlumpf/pyhx.git#v0.2.0"

    # latest 0.x release (update with `poetry update pyhx`)
    poetry add "git+https://github.com/cokeSchlumpf/pyhx.git#versions/0"
    ```

=== "pip"

    ```bash
    # exact release
    pip install "pyhx @ git+https://github.com/cokeSchlumpf/pyhx.git@v0.2.0"

    # latest 0.x release
    pip install "pyhx @ git+https://github.com/cokeSchlumpf/pyhx.git@versions/0"
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
