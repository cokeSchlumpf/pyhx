"""Mobile-viewport preview page — renders the app inside a 375×667 iframe."""

import htpy as y
import pyhx.components as c

from pyhx.core import WebAppRouter


router = WebAppRouter()


@router.page("/mobile-preview", title="Mobile Preview")
async def mobile_preview() -> y.Node:
    # Imported lazily to avoid a module-level cycle with main.home — main
    # imports this module to attach the router, and home() also needs to
    # link to mobile_preview from the index page.
    from samples.app_shell_layout.main import home

    return c.container(
        y.article[
            y.h1["Mobile Preview"],
            y.p[
                "The app rendered inside a 375×667 iframe (iPhone SE viewport). ",
                "The iframe is its own viewport, so the @media (max-width: 767px) rules fire naturally — ",
                "navigate the samples inside the frame to test each layout's drawer behavior at mobile size.",
            ],
            y.iframe(
                src=home.url(),
                style="width: 375px; height: 667px; border: 1px solid #ccc; display: block;",
            ),
        ],
        width="medium",
    )
