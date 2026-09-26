"""Text diff demo page."""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


@router.page("/text-diff", title="Text diff")
async def text_diff_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Text diff"],
            y.p[
                "A ",
                y.code["c.text_diff"],
                " renders a word-level, inline track-changes view between two ",
                "strings. Removed runs are wrapped in ",
                y.code["<del>"],
                " and inserted runs in ",
                y.code["<ins>"],
                " — both styled from design-system tokens (green for additions, ",
                "red for deletions), no inline styles.",
            ],
            y.h2["Word-level changes"],
            y.p[
                "Diffing is token-based, so single word swaps are highlighted ",
                "precisely while the surrounding text stays plain.",
            ],
            c.example(
                # docs:start basic
                y.div(style="margin-block: 1rem;")[
                    c.text_diff(
                        "The quick brown fox jumps over the lazy dog.",
                        "The quick red fox leaps over the sleepy dog.",
                    ),
                ],
                # docs:end basic
                code=[
                    ("code", src.text("basic"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Pure insertion and deletion"],
            y.p[
                "When text is only added or only removed, just the affected ",
                "runs are marked.",
            ],
            c.example(
                # docs:start add_remove
                y.div(
                    style="display: flex; flex-direction: column; gap: 1rem; margin-block: 1rem;"
                )[
                    c.text_diff(
                        "Send the report by Friday.",
                        "Send the final report by Friday afternoon.",
                    ),
                    c.text_diff(
                        "Please review and approve the draft today.",
                        "Please review the draft today.",
                    ),
                ],
                # docs:end add_remove
                code=[("code", src.text("add_remove"), "python")],
            ),
            y.h2["Paragraphs and line breaks"],
            y.p[
                "A blank line (",
                y.code["\\n\\n"],
                ") starts a new paragraph, while a single ",
                y.code["\\n"],
                " becomes a line break within the current paragraph.",
            ],
            c.example(
                # docs:start paragraphs
                y.div(style="margin-block: 1rem;")[
                    c.text_diff(
                        "Summary\nDraft version of the agreement.\n\n"
                        "Next steps: await sign-off.",
                        "Summary\nFinal version of the agreement.\n\n"
                        "Next steps: schedule the kickoff.",
                    ),
                ],
                # docs:end paragraphs
                code=[("code", src.text("paragraphs"), "python")],
            ),
        ]
    )
