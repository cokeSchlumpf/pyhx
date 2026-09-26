"""Drawer radio demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

from .drawer_select import COUNTRY_OPTIONS

src = snippets(__file__)


router = WebAppRouter()


@router.page("/drawer-radio", title="Drawer radio")
async def drawer_radio_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Drawer radio"],
            y.p[
                "A ",
                y.code["drawer_radio"],
                " is the single-selection sibling of ",
                y.code["drawer_select"],
                ", built for the same ",
                y.strong["long lists"],
                " of options. The on-page control shows the current selection ",
                "(or a placeholder); a button opens a drawer where the user ",
                "filters the full pool and ",
                y.strong["clicks one item to commit it"],
                " — the click selects the option and closes the drawer in one ",
                "step. Each demo below draws from a list of ",
                str(len(COUNTRY_OPTIONS)),
                " countries.",
            ],
            y.h2["Empty selection"],
            y.p[
                "Nothing selected yet — the control shows the placeholder. Open ",
                "the drawer, type to filter (e.g. ",
                y.code["ger"],
                ", ",
                y.code["united"],
                "), and click a row to select it.",
            ],
            c.example(
                # docs:start empty_selection
                y.div(style="margin-block: 1rem;")[
                    c.drawer_radio("country", COUNTRY_OPTIONS),
                ],
                # docs:end empty_selection
                code=[
                    ("code", src.text("empty_selection"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Pre-selected value"],
            y.p[
                "Pass ",
                y.code["value"],
                " as a single option value to seed the selection. The control ",
                "shows the label with a clear button next to it; clicking the ",
                "clear button resets it to the placeholder.",
            ],
            c.example(
                # docs:start preselected
                y.div(style="margin-block: 1rem;")[
                    c.drawer_radio("country-prefilled", COUNTRY_OPTIONS, value="de"),
                ],
                # docs:end preselected
                code=[("code", src.text("preselected"), "python")],
            ),
            y.h2["Custom labels"],
            y.p[
                "Every piece of user-facing text is configurable via ",
                y.code["DrawerRadioLabels"],
                ". The labels are stored on the component's state, so they ",
                "survive the htmx round-trips for filtering and selecting.",
            ],
            c.example(
                # docs:start custom_labels
                y.div(style="margin-block: 1rem;")[
                    c.drawer_radio(
                        "country-custom",
                        COUNTRY_OPTIONS,
                        value="jp",
                        labels=c.DrawerRadioLabels(
                            value_label="Country",
                            select_item_button="Choose country",
                            clear_item="Clear country",
                            no_item_selected="No country chosen yet.",
                            drawer_title="Pick a country",
                            query_label="Search countries",
                            available_items_column="All countries",
                            no_items_available="No countries match your search.",
                        ),
                    ),
                ],
                # docs:end custom_labels
                code=[("code", src.text("custom_labels"), "python")],
            ),
            y.h2["Disabled"],
            y.p[
                "Passing ",
                y.code["disabled=True"],
                " renders the trigger (and clear) buttons as disabled so the ",
                "selection cannot be changed, while the current value stays ",
                "visible.",
            ],
            c.example(
                # docs:start disabled
                y.div(style="margin-block: 1rem;")[
                    c.drawer_radio(
                        "country-disabled",
                        COUNTRY_OPTIONS,
                        value="gb",
                        disabled=True,
                    ),
                ],
                # docs:end disabled
                code=[("code", src.text("disabled"), "python")],
            ),
        ]
    )
