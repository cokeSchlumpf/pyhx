"""Conditional select demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


REGION_OPTIONS = [
    c.Option(label="Germany", value="de"),
    c.Option(label="France", value="fr"),
    c.Option(label="Italy", value="it"),
    c.Option(label="Spain", value="es"),
    c.Option(label="Netherlands", value="nl"),
    c.Option(label="Belgium", value="be"),
]


router = WebAppRouter()


@router.page("/conditional-select", title="Conditional select")
async def conditional_select_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Conditional select"],
            y.p[
                "A ",
                y.code["c.conditional_select"],
                " toggles between a default mode (selects nothing specific — the "
                "form submits an empty list under ",
                y.code["name"],
                ") and a ",
                y.em["specific"],
                " mode that reveals an inline multi-select for picking an explicit "
                "set. The revealed picker is configurable via ",
                y.code["control"],
                ".",
            ],
            y.h2['Default (control="drawer")'],
            y.p["Starts in ", y.code["all"], " mode — no picker shown."],
            c.example(
                # docs:start default_drawer
                c.conditional_select("regions_drawer", REGION_OPTIONS),
                # docs:end default_drawer
                code=[
                    ("code", src.text("default_drawer"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Specific preselection"],
            y.p[
                "Pass ",
                y.code['mode="specific"'],
                " and a ",
                y.code["value"],
                " to open on the picker with items already selected.",
            ],
            c.example(
                # docs:start specific_preselection
                c.conditional_select(
                    "regions_preselected",
                    REGION_OPTIONS,
                    value=["de", "fr"],
                    mode="specific",
                    labels=c.ConditionalSelectLabels(
                        drawer=c.DrawerSelectLabels(
                            value_column="Selected regions",
                            select_items_button="Select regions …",
                        ),
                    ),
                ),
                # docs:end specific_preselection
                code=[("code", src.text("specific_preselection"), "python")],
            ),
            y.h2['control="dropdown"'],
            y.p[
                "Toggling a checkbox in the dropdown does ",
                y.strong["not"],
                " collapse it — the re-render is scoped to the mode toggle.",
            ],
            c.example(
                # docs:start control_dropdown
                c.conditional_select(
                    "regions_dropdown",
                    REGION_OPTIONS,
                    value=["it"],
                    mode="specific",
                    control="dropdown",
                ),
                # docs:end control_dropdown
                code=[("code", src.text("control_dropdown"), "python")],
            ),
            y.h2['control="checkbox"'],
            c.example(
                # docs:start control_checkbox
                c.conditional_select(
                    "regions_checkbox",
                    REGION_OPTIONS,
                    value=["es", "nl"],
                    mode="specific",
                    control="checkbox",
                    labels=c.ConditionalSelectLabels(fieldset_legend="Regions"),
                ),
                # docs:end control_checkbox
                code=[("code", src.text("control_checkbox"), "python")],
            ),
            y.h2["Custom labels"],
            c.example(
                # docs:start custom_labels
                c.conditional_select(
                    "regions_labelled",
                    REGION_OPTIONS,
                    control="dropdown",
                    labels=c.ConditionalSelectLabels(
                        all_option="Global",
                        specific_option="Pick regions",
                        placeholder="Choose regions …",
                    ),
                ),
                # docs:end custom_labels
                code=[("code", src.text("custom_labels"), "python")],
            ),
            y.h2["Inside a form"],
            y.p[
                "Submit to confirm the shape: in ",
                y.code["all"],
                " mode nothing is posted under ",
                y.code["name"],
                "; in ",
                y.code["specific"],
                " mode the chosen values are.",
            ],
            c.example(
                # docs:start inside_form
                y.form(method="get", style="margin-block: 1rem;")[
                    c.conditional_select("regions", REGION_OPTIONS, control="dropdown"),
                    y.div(style="margin-block: 1rem;")[
                        c.button("Submit", appearance="primary", type="submit"),
                    ],
                ],
                # docs:end inside_form
                code=[("code", src.text("inside_form"), "python")],
            ),
        ]
    )
