"""Two made-up documents of a case, drawn as SVG page images.

Each page is an SVG of 1240 × 1754 px (A4 at 150 dpi) served by the sample, so
the viewer gets real images with real sizes, as an app gets PNGs rendered from
a PDF. Marks are given in pixels of that image, as an OCR step would deliver
them, and converted with ``BoundingBox.from_pixels``; notes likewise with
``Point.from_pixels``.

The badges are the app's choice: here the number of values read on a page, in
the warning appearance when some of them need checking.
"""

from dataclasses import dataclass
from html import escape

import htpy as y
from fastapi import FastAPI, Response

from pyhx.components import Color
from pyhx.components.variants import Appearance
from pyhx.components.view_model.document_viewer import (
    Annotation,
    BoundingBox,
    Document,
    DocumentPage,
    Mark,
    MarkStyle,
    Note,
    PageBadge,
    Point,
)

WIDTH, HEIGHT = 1240, 1754

PERSON = MarkStyle(color=Color.hex("#0f766e"))
ADDRESS = MarkStyle(color=Color.hex("#1d4ed8"))
WORK = MarkStyle(color=Color.hex("#6d28d9"))
HEALTH = MarkStyle(color="info")
UNCERTAIN = MarkStyle(color="warning", look="fill-outline")
CONTRADICTION = MarkStyle(color="danger", look="fill-outline")
CONTEXT = MarkStyle(color="neutral", look="outline")
TO_CHECK = (UNCERTAIN, CONTRADICTION)


@dataclass(frozen=True)
class Field:
    label: str
    value: str
    x: int
    y: int
    width: int
    mark: tuple[str, str, MarkStyle] | None = None
    """``(id, label, style)`` of the mark on the value, if any."""


@dataclass(frozen=True)
class SamplePage:
    heading: str
    fields: tuple[Field, ...]


@dataclass(frozen=True)
class SampleDocument:
    id: str
    title: str
    subtitle: str
    form_title: str
    page_count: int
    pages: dict[int, SamplePage]


@dataclass(frozen=True)
class SampleNote:
    id: str
    document: str
    page: int
    x: int
    y: int
    label: str
    author: str
    text: str
    color: Appearance | Color = "warning"


DOCUMENTS: tuple[SampleDocument, ...] = (
    SampleDocument(
        "anmeldung",
        "IV-Anmeldung 001.001",
        "Received 21.06.2026",
        "Anmeldung für Erwachsene: Berufliche Integration/Rente",
        12,
        {
            1: SamplePage(
                "1. Personalien",
                (
                    Field("Name", "Meier", 100, 250, 1040, ("name", "Name", PERSON)),
                    Field(
                        "Vornamen",
                        "DAVID",
                        100,
                        345,
                        1040,
                        ("vornamen", "First names", PERSON),
                    ),
                    Field(
                        "Geburtsdatum",
                        "14.08.1978",
                        100,
                        440,
                        500,
                        ("geburtsdatum", "Date of birth", PERSON),
                    ),
                    Field(
                        "AHV-Nummer",
                        "756.1978.0814.05",
                        640,
                        440,
                        500,
                        ("ahv", "AHV number", PERSON),
                    ),
                    Field("PLZ", "8000", 100, 535, 240, ("plz", "Postcode", ADDRESS)),
                    Field(
                        "Ort", "Musterstadt", 380, 535, 760, ("ort", "Place", ADDRESS)
                    ),
                    Field(
                        "Strasse",
                        "Hardstrasse",
                        100,
                        630,
                        820,
                        ("strasse", "Street", ADDRESS),
                    ),
                    Field(
                        "Nr.",
                        "12",
                        960,
                        630,
                        180,
                        ("hausnummer", "House number", ADDRESS),
                    ),
                    Field("Telefonnummer", "079 555 12 34", 100, 725, 500),
                    Field("E-Mail", "david.meier@example.ch", 640, 725, 500),
                ),
            ),
            2: SamplePage(
                "2. Familie",
                (
                    Field(
                        "Zivilstand",
                        "verheiratet seit 22.08.2010",
                        100,
                        250,
                        1040,
                        ("zivilstand", "Marital status", PERSON),
                    ),
                ),
            ),
            6: SamplePage(
                "4.3 Arbeitsunfähigkeit",
                (
                    Field(
                        "von",
                        "28.04.2026",
                        100,
                        250,
                        500,
                        ("au-von", "Incapacity since (low confidence)", UNCERTAIN),
                    ),
                    Field(
                        "in %",
                        "100",
                        640,
                        250,
                        500,
                        ("au-grad", "Incapacity in % (low confidence)", UNCERTAIN),
                    ),
                ),
            ),
            9: SamplePage(
                "5.4 Erwerbstätigkeit",
                (
                    Field(
                        "Berufsbezeichnung/Funktion",
                        "Bauleiter",
                        100,
                        250,
                        780,
                        ("beruf", "Occupation", WORK),
                    ),
                    Field(
                        "Pensum in %",
                        "100",
                        920,
                        250,
                        220,
                        ("pensum", "Workload", WORK),
                    ),
                    Field(
                        "von",
                        "01.03.2014",
                        100,
                        345,
                        500,
                        ("seit", "Employed since", WORK),
                    ),
                    Field(
                        "Name und Adresse des Arbeitgebenden",
                        "Muster Bau AG, Hauptstrasse 12, 8000 Musterstadt",
                        100,
                        440,
                        1040,
                        ("arbeitgeber", "Employer", CONTEXT),
                    ),
                ),
            ),
        },
    ),
    SampleDocument(
        "arztbericht",
        "Arztbericht Dr. Keller",
        "Received 21.07.2026",
        "Arztbericht zur IV-Anmeldung",
        3,
        {
            1: SamplePage(
                "1. Diagnose",
                (
                    Field(
                        "Diagnose",
                        "Mittelgradige depressive Episode (F32.1)",
                        100,
                        250,
                        1040,
                        ("diagnose", "Diagnosis", HEALTH),
                    ),
                    Field(
                        "Arbeitsunfähigkeit",
                        "100% seit 23.04.2026",
                        100,
                        345,
                        1040,
                        (
                            "au-arzt",
                            "Incapacity according to the doctor (contradicts the registration)",
                            CONTRADICTION,
                        ),
                    ),
                    Field(
                        "Behandlung seit",
                        "23.04.2026",
                        100,
                        440,
                        500,
                        ("behandlung", "In treatment since", HEALTH),
                    ),
                ),
            ),
        },
    ),
)

NOTES: tuple[SampleNote, ...] = (
    SampleNote(
        "note-adresse",
        "anmeldung",
        1,
        1100,
        640,
        "Address",
        "C. Morel, 24.06.2026",
        "The register of residents lists Hardstrasse 14. Ask at the first interview which number is right.",
    ),
    SampleNote(
        "note-au",
        "anmeldung",
        6,
        1100,
        300,
        "Start of incapacity",
        "C. Morel, 24.06.2026",
        "Handwritten and hard to read: 28.04. or 23.04.? Compare with the family doctor's certificate.",
        "danger",
    ),
    SampleNote(
        "note-arbeitgeber",
        "anmeldung",
        9,
        1100,
        500,
        "Employer",
        "R. Keller, 25.06.2026",
        "Employer questionnaire sent on 25.06.2026, answer expected by 15.07.2026.",
        "info",
    ),
    SampleNote(
        "note-arzt",
        "arztbericht",
        1,
        1100,
        395,
        "Incapacity since 23.04.",
        "C. Morel, 22.07.2026",
        "The doctor confirms 23.04.2026; the registration probably says 23.04. as well. Correct the value of the registration.",
        "danger",
    ),
)
"""Notes of the case workers; the viewer draws their pins, the sample's aside their content."""

VALUES: list[tuple[str, str, str, str]] = [
    (field.mark[0], field.mark[1], field.value, f"{document.title}, p. {number}")
    for document in DOCUMENTS
    for number, page in sorted(document.pages.items())
    for field in page.fields
    if field.mark
]
"""``(mark id, label, value, where)`` of every marked value, for the sample's aside."""


def find_document(document_id: str) -> SampleDocument | None:
    return next((d for d in DOCUMENTS if d.id == document_id), None)


def _value_box(field: Field) -> tuple[int, int, int, int]:
    """Pixel box around the value text of a field."""
    return (
        field.x + 4,
        field.y + 38,
        min(field.width - 8, 16 * len(field.value) + 20),
        44,
    )


def page_svg(document: SampleDocument, number: int) -> str:
    """The SVG image of page ``number`` (1-based) of ``document``."""
    page = document.pages.get(number)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#fff"/>',
        f'<text x="100" y="120" font-size="34" font-weight="700" fill="#18181b">{escape(document.form_title)}</text>',
        '<rect x="100" y="150" width="1040" height="3" fill="#18181b"/>',
    ]
    y = 220
    if page:
        parts.append(
            f'<text x="100" y="205" font-size="26" font-weight="700" fill="#18181b">{escape(page.heading)}</text>'
        )
        for field in page.fields:
            parts += [
                f'<text x="{field.x}" y="{field.y + 22}" font-size="20" font-weight="600" fill="#18181b">{escape(field.label)}</text>',
                f'<rect x="{field.x}" y="{field.y + 32}" width="{field.width}" height="56" rx="4" fill="none" stroke="#52525b" stroke-width="2"/>',
                f'<text x="{field.x + 12}" y="{field.y + 70}" font-size="26" fill="#1e3a8a">{escape(field.value)}</text>',
            ]
        y = max(f.y for f in page.fields) + 160
    for i, line_y in enumerate(range(y, 1560, 44)):
        width = (1040, 960, 1010, 720, 1040, 880)[i % 6]
        parts.append(
            f'<rect x="100" y="{line_y}" width="{width}" height="14" rx="2" fill="#e4e4e7"/>'
        )
    parts.append(
        f'<text x="1140" y="1660" font-size="18" text-anchor="end" fill="#52525b">Seite {number} / {document.page_count}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _page(document: SampleDocument, number: int) -> DocumentPage:
    page = document.pages.get(number)
    annotations: list[Annotation] = []
    marks = [field.mark for field in page.fields if field.mark] if page else []
    for field in page.fields if page else ():
        if field.mark:
            id_, label, style = field.mark
            x, y, w, h = _value_box(field)
            box = BoundingBox.from_pixels(
                x=x, y=y, width=w, height=h, page_width=WIDTH, page_height=HEIGHT
            )
            annotations.append(Mark(id=id_, label=label, box=box, style=style))
    for note in NOTES:
        if note.document == document.id and note.page == number:
            at = Point.from_pixels(
                x=note.x, y=note.y, page_width=WIDTH, page_height=HEIGHT
            )
            annotations.append(
                Note(
                    id=note.id,
                    label=note.label,
                    at=at,
                    color=note.color,
                    # any attributes of the app: here HTMX loads the note into the aside
                    attrs={
                        "hx-get": f"/sample-notes/{note.id}",
                        "hx-target": "#sample-note-detail",
                    },
                )
            )
    # docs:start badges
    # The badge is the app's choice: here the number of values read on the page,
    # in the warning appearance when some of them need checking.
    to_check = sum(1 for _, _, style in marks if style in TO_CHECK)
    badge = (
        PageBadge(
            text=str(len(marks)),
            label=f"{len(marks)} values, {to_check} to check"
            if to_check
            else f"{len(marks)} values",
            appearance="warning" if to_check else "neutral",
        )
        if marks
        else None
    )
    # docs:end badges
    return DocumentPage(
        src=f"/sample-pages/{document.id}/{number}.svg",
        width=WIDTH,
        height=HEIGHT,
        annotations=tuple(annotations),
        badge=badge,
    )


def sample_documents() -> list[Document]:
    return [
        Document(
            id=document.id,
            title=document.title,
            subtitle=document.subtitle,
            pages=tuple(_page(document, n) for n in range(1, document.page_count + 1)),
        )
        for document in DOCUMENTS
    ]


def page_url(document_id: str, number: int) -> str:
    """URL of a page image served by the sample."""
    return f"/sample-pages/{document_id}/{number}.svg"


def registration() -> Document:
    """The registration form (12 pages) with its marks, notes and badges."""
    return sample_documents()[0]


def medical_report() -> Document:
    """The medical report (3 pages) with its marks, notes and badges."""
    return sample_documents()[1]


def register_routes(app: FastAPI) -> None:
    """Serve the page images and the notes of the samples (also used by samples/canvas_layout)."""

    @app.get("/sample-pages/{document_id}/{number}.svg")
    async def sample_page(document_id: str, number: int) -> Response:
        document = find_document(document_id)
        if document is None or not 1 <= number <= document.page_count:
            return Response(status_code=404)
        return Response(page_svg(document, number), media_type="image/svg+xml")

    @app.get("/sample-notes/{note_id}")
    async def sample_note(note_id: str) -> Response:
        note = next((n for n in NOTES if n.id == note_id), None)
        if note is None:
            return Response(status_code=404)
        title = next(d.title for d in DOCUMENTS if d.id == note.document)
        fragment = y.div[
            y.strong[note.label],
            y.small[f"{note.author} · {title}, p. {note.page}"],
            y.p[note.text],
            y.small["loaded with hx-get from the pin"],
        ]
        return Response(str(fragment), media_type="text/html")
