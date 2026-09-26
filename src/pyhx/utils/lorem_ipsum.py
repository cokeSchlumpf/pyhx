import random

import htpy as y

_LOREM_WORDS = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "in",
    "reprehenderit",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
]


def lorem_ipsum(
    min_words: int = 42,
    max_words: int = 67,
    paragraphs: int | None = None,
) -> y.Node:
    """Return one or more `<p>` paragraphs of placeholder lorem ipsum text.

    Each paragraph contains a random word count in `[min_words, max_words]`.
    When `paragraphs` is None, a single paragraph is returned.
    """
    count = 1 if paragraphs is None else paragraphs

    min_words = min(min_words, max_words)

    def _paragraph() -> str:
        n = random.randint(min_words, max_words)
        words = [random.choice(_LOREM_WORDS) for _ in range(n)]
        words[0] = words[0].capitalize()
        return " ".join(words) + "."

    return y.fragment[[y.p[_paragraph()] for _ in range(count)]]
