"""Dropdown demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


VIEW_OPTIONS = (
    c.Option(label="List", value="list"),
    c.Option(label="Grid", value="grid"),
    c.Option(label="Kanban", value="kanban"),
    c.Option(label="Calendar", value="calendar"),
)


PRIORITY_OPTIONS = (
    c.Option(label="Low", value="low"),
    c.Option(label="Medium", value="medium"),
    c.Option(label="High", value="high"),
    c.Option(label="Critical", value="critical"),
)


TAG_OPTIONS = (
    c.Option(label="Bug", value="bug"),
    c.Option(label="Feature", value="feature"),
    c.Option(label="Docs", value="docs"),
    c.Option(label="Chore", value="chore"),
)


router = WebAppRouter()


@router.page("/dropdown", title="Dropdown")
async def dropdown_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Dropdown"],
            y.p[
                "A dropdown is built on the native ",
                y.code["<details>"],
                " / ",
                y.code["<summary>"],
                " element (Pico's ",
                y.code[".dropdown"],
                " styling). ",
                y.code["c.dropdown_radio"],
                " is the single-select variant, ",
                y.code["c.dropdown_checkbox"],
                " is the multi-select variant — both submit as a normal form ",
                "field and need no JavaScript to open or close. The visible ",
                "summary label is refreshed on every change via a small htmx ",
                "fragment.",
            ],
            y.h2["Single-select (radio)"],
            c.example(
                # docs:start radio_basic
                y.div(style="margin-block: 1rem; max-width: 300px;")[
                    c.dropdown_radio("view", VIEW_OPTIONS),
                ],
                # docs:end radio_basic
                code=[
                    ("code", src.text("radio_basic"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Single-select with pre-selection"],
            c.example(
                # docs:start radio_preselect
                y.div(style="margin-block: 1rem; max-width: 300px;")[
                    c.dropdown_radio("priority", PRIORITY_OPTIONS, value="medium"),
                ],
                # docs:end radio_preselect
                code=[("code", src.text("radio_preselect"), "python")],
            ),
            y.h2["Multi-select (checkbox)"],
            y.p[
                "The summary lists every selected option, comma-separated. ",
                "Falls back to the placeholder when nothing is selected.",
            ],
            c.example(
                # docs:start checkbox_basic
                y.div(style="margin-block: 1rem; max-width: 300px;")[
                    c.dropdown_checkbox("tags", TAG_OPTIONS),
                ],
                # docs:end checkbox_basic
                code=[("code", src.text("checkbox_basic"), "python")],
            ),
            y.h2["Multi-select with pre-selection"],
            c.example(
                # docs:start checkbox_preselect
                y.div(style="margin-block: 1rem; max-width: 300px;")[
                    c.dropdown_checkbox(
                        "tags-prefilled",
                        TAG_OPTIONS,
                        value=("bug", "docs"),
                        placeholder="Pick tags",
                    ),
                ],
                # docs:end checkbox_preselect
                code=[("code", src.text("checkbox_preselect"), "python")],
            ),
            y.h2["Inside a form"],
            y.p[
                "Submit the form to see the values land in the URL — radios as ",
                y.code["priority=..."],
                ", checkboxes as repeated ",
                y.code["tags=..."],
                " entries.",
            ],
            c.example(
                # docs:start in_form
                y.form(method="get", style="margin-block: 1rem;")[
                    y.div(
                        style="display: flex; align-items: center; gap: 1rem; max-width: 600px;"
                    )[
                        c.dropdown_radio("priority-form", PRIORITY_OPTIONS),
                        c.dropdown_checkbox("tags-form", TAG_OPTIONS),
                        c.button("Submit", appearance="primary", type="submit"),
                    ]
                ],
                # docs:end in_form
                code=[("code", src.text("in_form"), "python")],
            ),
        ]
    )
