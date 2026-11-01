# Editing patterns

pyhx offers three ways to let users change data. Pick by how much is edited at once and what must stay visible while editing.

| Pattern | When | Building block |
| --- | --- | --- |
| Edit drawer | Small records edited as a form: master data, creating a case, the status and customer of a case | `c.DataPage(..., can_edit=True)` |
| Detail page | The record is a workspace of its own: documents, summary, actions; a row click opens the page, not the drawer | `c.DataPage(..., can_edit=lambda item: FragmentResponse.redirect(...))` |
| Inline | Single values corrected one at a time while something else stays visible, e.g. values extracted from a document next to the document | `c.InlineEdit[T]` |

## Edit drawer

`DataPage` and `DataSection` open a `DataForm` for the clicked item in a drawer when `can_edit=True` (the default). The drawer covers part of the page and edits the whole record; the form is generated from the Pydantic model and its `@form` annotations.

## Detail page

When a record needs more room than a drawer, pass a callable as `can_edit`: it receives the clicked item and returns what the click renders, typically a redirect to the record's own page:

```python
c.DataPage(..., can_edit=lambda item: FragmentResponse.redirect(f"/cases/{item.id}"))
```

The detail page is an ordinary page, e.g. cards in a `c.split_layout`; values on it can be edited inline (below).

## Inline

`InlineEdit[T]` shows one value of a record (label, value, optional hint and source) with an edit button. The button loads a small form into the item; Enter or the save button validates the input against the model `T` and hands it to the app's `save` callback; the item then shows the saved value again. Errors stay at the field. Esc or the cancel button drops the form without a request.

```python
import htpy as y
from pydantic import BaseModel, Field

import pyhx.components as c


class Pensum(BaseModel):
    value: int = Field(ge=0, le=100)


async def load_pensum(key: str) -> Pensum:
    return Pensum(value=await repository.pensum(key))


async def save_pensum(key: str, value: Pensum) -> Pensum:
    await repository.set_pensum(key, value.value)
    return value


pensum = c.InlineEdit[Pensum](
    routes=router,
    name="pensum",
    type=Pensum,
    label="Pensum",
    load=load_pensum,
    save=save_pensum,
    display=lambda v: f"{v.value}%",
    source=lambda key, v: y.a(href=f"/documents/{key}#page-9")["Anmeldung S. 9"],
)


@router.page("/cases/{case_id}")
async def case(case_id: str) -> y.Node:
    return c.card[
        c.card.list(data_hx_inline_edit_group="extracted")[
            c.card.item[await pensum.render(case_id)],
        ],
    ]
```

- One instance per kind of value; the record is chosen per render by its `key`, which the edit and save requests carry. The server keeps no state.
- `T` holds one field, or a few that belong together (e.g. a degree and a date). The default form has a text, number or date input per field; `fields=lambda ctx: ...` renders other controls, with `c.form_field(..., error_text=ctx.visible_errors.get(name))` for the errors.
- `save` returns the value to display. It may raise a `pydantic.ValidationError` (e.g. for a rule the model can't check); its messages show at the fields.
- `hint(key, value)` adds a short remark next to the label (e.g. "unsicher gelesen"), `source(key, value)` a line below the value. Both are called again after a save, so they can change with the value.
- Only one item of a group is in edit mode: opening one cancels the open one. A group is the nearest element with `data-hx-inline-edit-group`; without one, the page is the group.
- The edit button is a real button with the accessible name `"<edit_label>: <label>"`; focus moves into the field when the form opens and back to the button when it closes. `save_label`, `cancel_label`, `edit_label` and `shortcuts_hint` set the texts.

The samples show it in both designs: the dossier page of `samples/canvas_layout` (`/dossier`) and the "Inline Edit" page of `samples/components`.
