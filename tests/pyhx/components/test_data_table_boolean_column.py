"""A boolean column shows Yes/No in the request's language."""

from typing import Annotated

import htpy as y
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

import pyhx.components.data.annotations as a
from pyhx.components.data.data_table import DataTable
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core import WebApp


class Member(BaseModel):
    id: str
    name: Annotated[str, a.TextColumn(label="Name")]
    active: Annotated[bool, a.BooleanColumn(label="Active")]


def _client() -> TestClient:
    hx = WebApp()
    rows = [
        Member(id="1", name="Ann", active=True),
        Member(id="2", name="Ben", active=False),
    ]
    table = DataTable(
        routes=hx, name="members", type=Member, source=SimpleDataSource(rows)
    )

    @hx.page("/members", title="Members")
    async def page() -> y.Node:
        return await table.render()

    return TestClient(hx.create_app())


@pytest.mark.parametrize(
    ("lang", "yes", "no"),
    [
        ("en", "Yes", "No"),
        ("de", "Ja", "Nein"),
        ("it", "Sì", "No"),
        ("fr", "Oui", "Non"),
    ],
)
def test_boolean_cells_are_translated(lang, yes, no):
    text = _client().get("/members", headers={"Accept-Language": lang}).text

    assert f"<span>{yes}</span>" in text and f"<span>{no}</span>" in text
    assert "<span>yes</span>" not in text
