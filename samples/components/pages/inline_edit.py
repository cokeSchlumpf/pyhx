"""Inline edit demo page.

``InlineEdit`` shows a single value with an edit button and edits it in
place: Enter saves, Esc cancels, errors stay at the field. This sample runs in
AppShell (default design); see ``samples/canvas_layout`` (dossier page) for
the canvas design.
"""

import datetime

import htpy as y
from pydantic import BaseModel, Field

# docs:start imports
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)

router = WebAppRouter()

_PROJECTS: dict[str, dict] = {
    "apollo": {
        "owner": "Ada Lovelace",
        "budget": 120,
        "due": datetime.date(2026, 12, 18),
    },
}


# docs:start model
class Budget(BaseModel):
    value: int = Field(ge=0, le=1000, description="Budget in kCHF")


async def load_budget(key: str) -> Budget:
    return Budget(value=_PROJECTS[key]["budget"])


async def save_budget(key: str, value: Budget) -> Budget:
    _PROJECTS[key]["budget"] = value.value
    return value


budget = c.InlineEdit[Budget](
    routes=router,
    name="budget",
    type=Budget,
    label="Budget",
    load=load_budget,
    save=save_budget,
    display=lambda v: f"{v.value} kCHF",
    source=lambda key, v: "Approved by the steering board",
)
# docs:end model


class Owner(BaseModel):
    value: str = Field(min_length=3)


async def _load_owner(key: str) -> Owner:
    return Owner(value=_PROJECTS[key]["owner"])


async def _save_owner(key: str, value: Owner) -> Owner:
    _PROJECTS[key]["owner"] = value.value
    return value


owner = c.InlineEdit[Owner](
    routes=router,
    name="owner",
    type=Owner,
    label="Owner",
    load=_load_owner,
    save=_save_owner,
)


class Due(BaseModel):
    value: datetime.date


async def _load_due(key: str) -> Due:
    return Due(value=_PROJECTS[key]["due"])


async def _save_due(key: str, value: Due) -> Due:
    _PROJECTS[key]["due"] = value.value
    return value


due = c.InlineEdit[Due](
    routes=router,
    name="due",
    type=Due,
    label="Due date",
    load=_load_due,
    save=_save_due,
    display=lambda v: v.value.strftime("%d %b %Y"),
    hint=lambda key, v: "soon" if v.value < datetime.date(2027, 1, 1) else None,
)


@router.page("/inline-edit", title="Inline Edit")
async def inline_edit_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Inline Edit"],
            y.p[
                y.code["InlineEdit[T]"],
                " shows one value with an edit button and edits it in place. ",
                "The form validates against the Pydantic model ",
                y.code["T"],
                " and hands the value to the app's ",
                y.code["save"],
                " callback; Enter saves, Esc cancels, errors stay at the field. ",
                "Opening another value of the same group cancels the open one.",
            ],
            c.example(
                # docs:start card
                c.card[
                    c.card.header[c.card.title[y.h3["Project Apollo"]]],
                    c.card.list(data_hx_inline_edit_group="project")[
                        c.card.item[await owner.render("apollo")],
                        c.card.item[await budget.render("apollo")],
                        c.card.item[await due.render("apollo")],
                    ],
                ],
                # docs:end card
                code=[
                    ("card", src.text("card"), "python"),
                    ("model", src.text("model"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
                max_height=None,
            ),
            c.markdown("""
                ## Parameters

                - `load(key)` returns the current value of a record, `save(key, value)`
                  saves the validated value and returns the one to display. `save` may
                  raise a `pydantic.ValidationError`; its messages show at the field.
                - `display(value)` formats the value; `source(key, value)` and
                  `hint(key, value)` add a source line and a short remark next to the label.
                - `fields(ctx)` renders other controls than the default text, number
                  or date input, with `form_field(error_text=ctx.visible_errors.get(...))`.
                - The default texts come translated in the language of the request;
                  `save_label`, `cancel_label`, `edit_label` and `shortcuts_hint` replace
                  them.

                Items in the same element with `data-hx-inline-edit-group` form a group;
                without one, the page is the group.
            """),
        ]
    )
