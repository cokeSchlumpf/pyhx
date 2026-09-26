"""File Dropzone demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

import humanize
from fastapi import File, UploadFile
from pyhx.core import WebAppRouter
from pyhx.core.primitives import htmx
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.fragment.post("/file-dropzone/upload")
async def upload(file: UploadFile = File(...)) -> y.Node:
    data = await file.read()
    return y.article(id="file-dropzone-result", **{"hx-swap-oob": "outerHTML"})[
        y.h3["Received"],
        y.p[
            f"{file.filename} - {file.content_type} - "
            f"{humanize.naturalsize(len(data))}"
        ],
    ]


@router.page("/file-dropzone", title="File Dropzone")
async def file_dropzone_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["File Dropzone"],
            y.p[
                "A bordered drag-and-drop file picker with a click-to-browse "
                "fallback. Renders only the picker surface - a real "
                "`<input type=\"file\">` under the hood - so it composes into "
                "any form the same way a plain file input would; it doesn't "
                "render its own submit button or own the surrounding form."
            ],
            y.h2["Basic"],
            c.example(
                # docs:start basic_demo
                y.form(
                    **htmx(
                        hx_post=upload.url(),
                        hx_encoding="multipart/form-data",
                        hx_swap="none",
                        as_dict=True,
                    )
                )[
                    c.file_dropzone(name="file"),
                    c.button("Upload", appearance="primary", type="submit"),
                ],
                # docs:end basic_demo
                code=[
                    ("code", src.text("basic_demo"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.article(id="file-dropzone-result")[
                y.h3["Received"],
                y.p["Drop or select a file and click Upload to see it here."],
            ],
            y.h2["Multiple files"],
            c.example(
                # docs:start multiple_demo
                c.file_dropzone(name="files", multiple=True),
                # docs:end multiple_demo
                code=[("code", src.text("multiple_demo"), "python")],
            ),
            y.h2["Disabled"],
            c.example(
                # docs:start disabled_demo
                c.file_dropzone(name="file", disabled=True),
                # docs:end disabled_demo
                code=[("code", src.text("disabled_demo"), "python")],
            ),
        ],
        width="medium",
    )
