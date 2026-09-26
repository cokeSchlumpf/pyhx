from uuid import uuid4

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from .button import button


@component
def file_dropzone(
    name: str,
    *,
    id: str | None = None,
    accept: str | None = None,
    multiple: bool = False,
    disabled: bool = False,
    required: bool = False,
    placeholder: str = "Drag & drop a file here, or click to browse",
    **kwargs,
) -> y.Node:
    """A drag-and-drop file picker wrapping a file.

    Renders only the picker surface (no submit button). Behaviour is wired up by ``pyhx.file-dropzone.js``.

    Args:
        name: Form field name, set on the underlying input.
        id: Root element id; defaults to a random one.
        accept: Accepted file types, as the ``accept`` attribute.
        multiple: Allow selecting more than one file.
        disabled: Dim the box and block interaction.
        required: Set on the input, for native form validation.
        placeholder: Text shown on the surface.
        **kwargs: Extra attributes for the root element.
    """
    dropzone_id = id or f"hx-file-dropzone-{uuid4().hex}"
    select_label = "Select Files" if multiple else "Select File"

    return y.div(
        id=dropzone_id,
        data_file_dropzone=True,
        **classnames(
            {"hx-file-dropzone": True, "hx-file-dropzone--disabled": disabled},
            **kwargs,
        ),
    )[
        y.input(
            type="file",
            name=name,
            accept=accept,
            multiple=multiple,
            disabled=disabled,
            required=required,
            data_file_dropzone_input=True,
            class_="hx-file-dropzone__input",
        ),
        y.div(class_="hx-file-dropzone__surface")[
            y.i(data_feather="upload-cloud", class_="hx-file-dropzone__icon"),
            y.p(
                data_file_dropzone_placeholder=True,
                class_="hx-file-dropzone__placeholder",
            )[placeholder],
            button(
                select_label,
                type="button",
                variant="outline",
                size="sm",
                disabled=disabled,
                data_file_dropzone_browse=True,
            ),
        ],
    ]
