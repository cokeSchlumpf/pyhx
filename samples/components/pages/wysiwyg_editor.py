"""WYSIWYG Editor demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from typing import Annotated
from markupsafe import Markup

from fastapi import Form
from pyhx.core import WebAppRouter
from pyhx.core.primitives import htmx
from pyhx.components.primitives.wysiwyg_editor import sanitize_wysiwyg_html
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()

@router.fragment.post("/wysiwyg-editor/preview")
async def preview(
    description: Annotated[str, Form()] = "",
) -> y.Node:
    safe_description = sanitize_wysiwyg_html(description)

    return y.article(id="wysiwyg-editor-preview", **{"hx-swap-oob": "outerHTML"})[
        y.h3["Rendered preview"],
        y.div(class_="hx-wysiwyg-editor-preview")[Markup(safe_description)],
        y.h4["Raw submitted HTML"],
        y.pre[y.code[description]],
    ]

@router.page("/wysiwyg-editor", title="WYSIWYG Editor")
async def wysiwyg_editor_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["WYSIWYG Editor"],
            y.p[
                "Lightweight rich-text editor with toolbar, contenteditable input, "
                "and hidden form field for HTML submission."
            ],
            c.example(
                # docs:start editor_demo
                y.form(
                    **htmx(
                        hx_post=preview.url(),
                        hx_target="#wysiwyg-editor-preview",
                        hx_swap="outerHTML",
                        as_dict=True,
                    )
                )[
                    c.wysiwyg_editor(
                        name="description",
                        value="<p>Hello <strong>World</strong></p>",
                    ),
                    c.button("Submit", appearance="primary", type="submit"),
                ],
                # docs:end editor_demo
                code=[
                    ("code", src.text("editor_demo"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.article(id="wysiwyg-editor-preview")[
                y.h3["Submitted value"],
                y.p["Submit the form to see the posted HTML value."],
            ],
        ],
        width="medium",
    )
