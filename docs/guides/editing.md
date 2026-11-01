# Editing patterns

pyhx offers three ways to let users change data. Pick by how much is edited at once and what must stay visible while editing.

| Pattern | When | Building block |
| --- | --- | --- |
| Edit drawer | Small records edited as a form: master data, creating a case, the status and customer of a case | `c.DataPage(..., can_edit=True)` |
| Detail page | The record is a workspace of its own: documents, summary, actions; a row click opens the page, not the drawer | `c.DataPage(..., can_edit=lambda item: FragmentResponse.redirect(...))` |
| Inline | Single values corrected one at a time while something else stays visible, e.g. values extracted from a document next to the document | `c.InlineEdit[T]` |

## Edit drawer

`DataPage` and `DataSection` open a `DataForm` for the clicked item in a drawer when `can_edit=True` (the default). The drawer covers part of the page and edits the whole record; the form is generated from the Pydantic model and its `@form` annotations.

- The drawer keeps its header on top and its footer (delete on the left, cancel and submit on the right) at the bottom while the form scrolls, in both designs; the page behind it doesn't scroll.
- In the canvas design the drawer's form is compact (32px fields, 28px buttons, labels left where a field has room). `form_size` and `form_label_position` on `DataPage` and `DataSection` override that for both the edit and the create drawer, e.g. `form_label_position="top"` for a form that keeps its two columns. See [Layouts: DataPage and drawers](layouts.md#datapage-and-drawers).
- The list side of the page has quick filters, a search field and a footer with the number of items, see [Data Tables](data-tables.md).

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
- The edit button is a real button with the accessible name "Edit <label>"; focus moves into the field when the form opens and back to the button when it closes.
- The form's size follows its place like other forms: in the canvas design it is compact in the aside of a `split_layout` or in a drawer (32px fields, 28px buttons) and full size in the main column. `size="sm"` or `"md"` overrides the place, `label_position` places the labels of a form with several fields (see [Layouts: Compact forms](layouts.md#compact-forms)). A single field has no label of its own: the item's label names it.
- The default texts ("Save", "Cancel", "Edit <label>", the keyboard hint) come translated from pyhx's catalogs in the language of the request; `save_label`, `cancel_label`, `edit_label` (the button's whole accessible name) and `shortcuts_hint` (`None` hides it) replace them.

The samples show it in both designs: the dossier page of `samples/canvas_layout` (`/dossier`) and the "Inline Edit" page of `samples/components`.
