"""Drawer select demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


# A deliberately long pool — the drawer select exists precisely for lists
# like this, where an inline dropdown or a wall of checkboxes would be
# unusable and the user needs to filter down to the few items they want.
COUNTRY_OPTIONS = tuple(
    c.Option(label=label, value=value)
    for value, label in (
        ("ar", "Argentina"),
        ("au", "Australia"),
        ("at", "Austria"),
        ("be", "Belgium"),
        ("br", "Brazil"),
        ("bg", "Bulgaria"),
        ("ca", "Canada"),
        ("cl", "Chile"),
        ("cn", "China"),
        ("co", "Colombia"),
        ("hr", "Croatia"),
        ("cz", "Czechia"),
        ("dk", "Denmark"),
        ("eg", "Egypt"),
        ("ee", "Estonia"),
        ("fi", "Finland"),
        ("fr", "France"),
        ("de", "Germany"),
        ("gr", "Greece"),
        ("hu", "Hungary"),
        ("is", "Iceland"),
        ("in", "India"),
        ("id", "Indonesia"),
        ("ie", "Ireland"),
        ("il", "Israel"),
        ("it", "Italy"),
        ("jp", "Japan"),
        ("ke", "Kenya"),
        ("lv", "Latvia"),
        ("lt", "Lithuania"),
        ("lu", "Luxembourg"),
        ("my", "Malaysia"),
        ("mx", "Mexico"),
        ("nl", "Netherlands"),
        ("nz", "New Zealand"),
        ("ng", "Nigeria"),
        ("no", "Norway"),
        ("pe", "Peru"),
        ("ph", "Philippines"),
        ("pl", "Poland"),
        ("pt", "Portugal"),
        ("ro", "Romania"),
        ("sa", "Saudi Arabia"),
        ("rs", "Serbia"),
        ("sg", "Singapore"),
        ("sk", "Slovakia"),
        ("si", "Slovenia"),
        ("za", "South Africa"),
        ("kr", "South Korea"),
        ("es", "Spain"),
        ("se", "Sweden"),
        ("ch", "Switzerland"),
        ("th", "Thailand"),
        ("tr", "Türkiye"),
        ("ua", "Ukraine"),
        ("ae", "United Arab Emirates"),
        ("gb", "United Kingdom"),
        ("us", "United States"),
        ("vn", "Vietnam"),
    )
)


router = WebAppRouter()


@router.page("/drawer-select", title="Drawer select")
async def drawer_select_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Drawer select"],
            y.p[
                "A ",
                y.code["c.drawer_select"],
                " is built for selecting from ",
                y.strong["long lists"],
                " of options. The on-page control shows only the current ",
                "selection; a ",
                y.em["Select items"],
                " button opens a drawer where the user types to filter the ",
                "full pool, clicks rows to stage them, and confirms. Each ",
                "demo below draws from a list of ",
                str(len(COUNTRY_OPTIONS)),
                " countries.",
            ],
            y.h2["Empty selection"],
            y.p[
                "Nothing selected yet. Open the drawer and start typing ",
                "(e.g. ",
                y.code["ger"],
                ", ",
                y.code["united"],
                ") to filter the list down before picking.",
            ],
            c.example(
                # docs:start empty_selection
                c.drawer_select("countries", COUNTRY_OPTIONS),
                # docs:end empty_selection
                code=[
                    ("code", src.text("empty_selection"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Pre-selected values"],
            y.p[
                "Pass ",
                y.code["value"],
                " as a list of option values to seed the current ",
                "selection. Selected items render in the control with a ",
                "remove button and are excluded from the drawer's available ",
                "list.",
            ],
            c.example(
                # docs:start prefilled
                c.drawer_select(
                    "countries-prefilled",
                    COUNTRY_OPTIONS,
                    value=["de", "fr", "us"],
                ),
                # docs:end prefilled
                code=[("code", src.text("prefilled"), "python")],
            ),
            y.h2["Custom labels"],
            y.p[
                "Every piece of user-facing text is configurable via ",
                y.code["DrawerSelectLabels"],
                ". The labels are stored on the component's state, so they ",
                "survive the htmx round-trips for filtering, adding, and ",
                "removing.",
            ],
            c.example(
                # docs:start custom_labels
                c.drawer_select(
                    "countries-custom",
                    COUNTRY_OPTIONS,
                    value=["jp"],
                    labels=c.DrawerSelectLabels(
                        value_column="Country",
                        select_items_button="Add countries",
                        drawer_title="Pick countries",
                        query_label="Search countries",
                        available_items_column="All countries",
                        selected_items_column="Picked countries",
                        select_button="Confirm selection",
                        no_items_available="No countries match your search.",
                        no_items_selected="No countries picked yet.",
                    ),
                ),
                # docs:end custom_labels
                code=[("code", src.text("custom_labels"), "python")],
            ),
            y.h2["Disabled"],
            y.p[
                "Passing ",
                y.code["disabled=True"],
                " renders the trigger button as disabled so the drawer ",
                "cannot be opened, while the current selection stays ",
                "visible.",
            ],
            c.example(
                # docs:start disabled
                c.drawer_select(
                    "countries-disabled",
                    COUNTRY_OPTIONS,
                    value=["gb", "ie"],
                    disabled=True,
                ),
                # docs:end disabled
                code=[("code", src.text("disabled"), "python")],
            ),
        ]
    )
