"""Grid demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


# Visible block used by the demos so layout/spans/alignment are obvious.
GRID_CELL_STYLE = (
    "background: var(--hx-color-neutral-200); "
    "padding: var(--hx-spacing-sm); "
    "border-radius: var(--hx-radius-sm); "
    "text-align: center; "
    "font-size: var(--hx-text-sm);"
)


router = WebAppRouter()


@router.page("/grid", title="Grid")
async def grid_page() -> y.Node:
    def demo_cell(
        text: str,
        *,
        span: int | str | None = None,
        align: str | None = None,
        extra_style: str = "",
    ) -> y.Node:
        classes: list[str] = []
        if span is not None:
            classes.append(f"hx-grid-span-{span}")
        if align is not None:
            classes.append(f"hx-grid-align-{align}")
        return y.div(
            class_=" ".join(classes) or None,
            style=GRID_CELL_STYLE + extra_style,
        )[text]

    return c.container(
        y.article[
            y.h1["Grid"],
            y.p[
                "The ",
                y.code["hx-grid"],
                " class is a CSS-only layout utility — apply it to any "
                "container (",
                y.code["div"],
                ", ",
                y.code["form"],
                ", ",
                y.code["section"],
                ", …) and its direct children are laid out on a 12-column grid. "
                "No wrapper divs and no marker class on the children: each "
                "direct child is a cell.",
            ],
            y.p[
                "Three public custom properties tune the container: ",
                y.code["--hx-grid-columns"],
                " (default ",
                y.code["12"],
                "), ",
                y.code["--hx-grid-gap"],
                " (default ",
                y.code["--hx-spacing-md"],
                "), and ",
                y.code["--hx-grid-align"],
                " (default ",
                y.code["stretch"],
                "). Per-cell tweaks use utility classes on the child: ",
                y.code["hx-grid-span-{n}"],
                ", ",
                y.code["hx-grid-span-full"],
                ", and ",
                y.code["hx-grid-align-{top|center|bottom|stretch}"],
                ".",
            ],
            y.h2["Default — 12 columns"],
            y.p["Children fill columns left-to-right and wrap to new rows."],
            c.example(
                # docs:start default
                y.div(class_="hx-grid", style="margin-block: 1rem;")[
                    [demo_cell(str(n + 1)) for n in range(12)]
                ],
                # docs:end default
                code=[
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("default"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Custom columns and gap"],
            y.p[
                "Set ",
                y.code["--hx-grid-columns"],
                " and ",
                y.code["--hx-grid-gap"],
                " inline (or in a stylesheet) on the container.",
            ],
            c.example(
                # docs:start custom_columns
                y.div(
                    class_="hx-grid",
                    style=(
                        "--hx-grid-columns: 4; "
                        "--hx-grid-gap: var(--hx-spacing-xl); "
                        "margin-block: 1rem;"
                    ),
                )[[demo_cell(str(n + 1)) for n in range(8)]],
                # docs:end custom_columns
                code=[("code", src.text("custom_columns"), "python")],
            ),
            y.h2["Spanning columns"],
            y.p[
                "Add ",
                y.code["hx-grid-span-{n}"],
                " on a child to span ",
                y.code["n"],
                " columns, or ",
                y.code["hx-grid-span-full"],
                " to span the whole row.",
            ],
            c.example(
                # docs:start spanning
                y.div(class_="hx-grid", style="margin-block: 1rem;")[
                    demo_cell("span 6", span=6),
                    demo_cell("span 6", span=6),
                    demo_cell("span 4", span=4),
                    demo_cell("span 8", span=8),
                    demo_cell("span 3", span=3),
                    demo_cell("span 3", span=3),
                    demo_cell("span 3", span=3),
                    demo_cell("span 3", span=3),
                    demo_cell("span full", span="full"),
                ],
                # docs:end spanning
                code=[("code", src.text("spanning"), "python")],
            ),
            y.h2["Per-cell vertical alignment"],
            y.p[
                "Cells stretch to the row height by default. Add ",
                y.code["hx-grid-align-{top|center|bottom|stretch}"],
                " on a child to override it on a single cell. The first cell "
                "below is intentionally taller to make the alignment visible.",
            ],
            c.example(
                # docs:start per_cell_align
                y.div(
                    class_="hx-grid",
                    style="--hx-grid-columns: 4; margin-block: 1rem;",
                )[
                    demo_cell("tall", extra_style=" min-height: 6rem;"),
                    demo_cell("top", align="top"),
                    demo_cell("center", align="center"),
                    demo_cell("bottom", align="bottom"),
                ],
                # docs:end per_cell_align
                code=[("code", src.text("per_cell_align"), "python")],
            ),
            y.h2["Global vertical alignment"],
            y.p[
                "Set ",
                y.code["--hx-grid-align"],
                " on the container to align every cell in one place.",
            ],
            c.example(
                # docs:start global_align
                y.div(
                    class_="hx-grid",
                    style=(
                        "--hx-grid-columns: 4; "
                        "--hx-grid-align: center; "
                        "margin-block: 1rem;"
                    ),
                )[
                    demo_cell("tall", extra_style=" min-height: 6rem;"),
                    demo_cell("auto"),
                    demo_cell("auto"),
                    demo_cell("auto"),
                ],
                # docs:end global_align
                code=[("code", src.text("global_align"), "python")],
            ),
            y.h2["On a form"],
            y.p[
                "The grid works on any container — drop ",
                y.code["hx-grid"],
                " onto a ",
                y.code["form"],
                " and use spans for two-column / full-width fields.",
            ],
            c.example(
                # docs:start on_form
                y.form(
                    class_="hx-grid",
                    style="--hx-grid-columns: 2; margin-block: 1rem;",
                )[
                    y.label[
                        "First name",
                        y.input(type="text", name="first_name", style="width: 100%;"),
                    ],
                    y.label[
                        "Last name",
                        y.input(type="text", name="last_name", style="width: 100%;"),
                    ],
                    y.label(class_="hx-grid-span-full")[
                        "Email",
                        y.input(type="email", name="email", style="width: 100%;"),
                    ],
                    y.div(class_="hx-grid-span-full", style="text-align: right;")[
                        c.button("Submit", appearance="primary", icon="send"),
                    ],
                ],
                # docs:end on_form
                code=[("code", src.text("on_form"), "python")],
            ),
        ]
    )
