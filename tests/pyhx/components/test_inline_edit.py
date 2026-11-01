import datetime
import re

import htpy as y
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

import pyhx.components as c
from pyhx.core import WebApp


class _Pensum(BaseModel):
    value: int = Field(ge=0, le=100)


class _Grad(BaseModel):
    degree: int = Field(ge=0, le=100, title="Grad")
    since: datetime.date | None = Field(default=None, title="Seit")


def _rejected(value: int) -> ValidationError:
    return ValidationError.from_exception_data(
        "Pensum",
        [
            InitErrorDetails(
                type=PydanticCustomError("rejected", "Not allowed for this case"),
                loc=("value",),
                input=value,
            )
        ],
    )


def _build() -> tuple[TestClient, dict[str, int], c.InlineEdit[_Pensum]]:
    hx = WebApp()
    store = {"case-1": 100, "case 2/b": 50}

    async def load(key: str) -> _Pensum:
        return _Pensum(value=store[key])

    async def save(key: str, value: _Pensum) -> _Pensum:
        if value.value == 13:
            raise _rejected(value.value)
        store[key] = value.value
        return value

    pensum = c.InlineEdit[_Pensum](
        routes=hx,
        name="pensum",
        type=_Pensum,
        label="Pensum",
        load=load,
        save=save,
        display=lambda v: f"{v.value}%",
        source=lambda key, v: y.a(href="#")["Anmeldung S. 9"],
        hint=lambda key, v: "unsicher gelesen" if v.value == 100 else None,
    )

    @hx.page("/", title="Home")
    async def home() -> y.Node:
        return y.div(data_hx_inline_edit_group="angaben")[await pensum.render("case-1")]

    return TestClient(hx.create_app()), store, pensum


@pytest.fixture
def app():
    return _build()


class TestDisplay:
    def test_renders_label_value_hint_and_source(self, app):
        client, _, _ = app
        html = client.get("/").text
        assert (
            '<div class="hx-inline-edit" id="hx-inline-edit--pensum--case-1">' in html
        )
        assert (
            '<span class="hx-inline-edit__label" id="hx-inline-edit--pensum--case-1__label">Pensum</span>'
            in html
        )
        assert '<span class="hx-inline-edit__value">100%</span>' in html
        assert '<span class="hx-inline-edit__hint">unsicher gelesen</span>' in html
        assert (
            '<span class="hx-inline-edit__source"><a href="#">Anmeldung S. 9</a></span>'
            in html
        )

    def test_edit_action_is_a_labelled_button(self, app):
        client, _, _ = app
        html = client.get("/").text
        button = re.search(r"<button[^>]*hx-inline-edit__edit[^>]*>", html)
        assert button is not None
        tag = button.group()
        assert 'type="button"' in tag
        assert 'aria-label="Edit Pensum"' in tag
        assert 'hx-get="/_components/inline-edit/pensum/edit?key=case-1"' in tag
        assert 'hx-target="#hx-inline-edit--pensum--case-1"' in tag
        assert 'hx-swap="beforeend"' in tag

    def test_no_hint_when_callback_returns_none(self):
        client, store, _ = _build()
        store["case-1"] = 80
        html = client.get("/").text
        assert "hx-inline-edit__hint" not in html
        assert '<span class="hx-inline-edit__value">80%</span>' in html

    def test_default_display_and_empty_value(self):
        hx = WebApp()

        async def load(key: str) -> _Grad:
            return _Grad.model_construct(degree=None, since=None)

        async def save(key: str, value: _Grad) -> _Grad:
            return value

        grad = c.InlineEdit[_Grad](
            routes=hx, name="grad", type=_Grad, label="Grad AU", load=load, save=save
        )

        @hx.page("/", title="Home")
        async def home() -> y.Node:
            return await grad.render(
                "x", _Grad(degree=50, since=datetime.date(2026, 4, 1))
            )

        @hx.page("/empty", title="Empty")
        async def empty() -> y.Node:
            return await grad.render("x")

        client = TestClient(hx.create_app())
        assert (
            '<span class="hx-inline-edit__value">50, 2026-04-01</span>'
            in client.get("/").text
        )
        assert (
            '<span class="hx-inline-edit__value">–</span>' in client.get("/empty").text
        )


class TestEditFragment:
    def test_returns_form_with_current_value(self, app):
        client, _, _ = app
        html = client.get(
            "/_components/inline-edit/pensum/edit", params={"key": "case-1"}
        ).text
        assert html.startswith(
            '<form class="hx-inline-edit__form" id="hx-inline-edit--pensum--case-1__form"'
        )
        assert 'aria-labelledby="hx-inline-edit--pensum--case-1__label"' in html
        assert (
            'hx-post="/_components/headless-form/inline-edit-pensum/submit?key=case-1"'
            in html
        )
        assert 'hx-swap="none"' in html
        # Initial render is delivered by a beforeend swap, so not out-of-band.
        assert "hx-swap-oob" not in html
        assert 'type="number"' in html
        assert 'value="100"' in html
        assert 'name="value"' in html

    def test_single_control_is_labelled_by_the_item_label(self, app):
        client, _, _ = app
        html = client.get(
            "/_components/inline-edit/pensum/edit", params={"key": "case-1"}
        ).text
        control = re.search(r"<input[^>]*name=\"value\"[^>]*>", html)
        assert control is not None
        assert (
            'aria-labelledby="hx-inline-edit--pensum--case-1__label"' in control.group()
        )

    def test_has_save_cancel_and_shortcuts(self, app):
        client, _, _ = app
        html = client.get(
            "/_components/inline-edit/pensum/edit", params={"key": "case-1"}
        ).text
        assert re.search(r'<button[^>]*type="submit"[^>]*>Save</button>', html)
        assert re.search(
            r'<button[^>]*type="button"[^>]*data-hx-inline-edit-cancel[^>]*>Cancel</button>',
            html,
        )
        assert "Esc cancels · ↵ saves" in html

    def test_cancel_needs_no_request(self, app):
        client, _, _ = app
        html = client.get(
            "/_components/inline-edit/pensum/edit", params={"key": "case-1"}
        ).text
        cancel = re.search(r"<button[^>]*data-hx-inline-edit-cancel[^>]*>", html)
        assert cancel is not None
        assert "hx-get" not in cancel.group() and "hx-post" not in cancel.group()

    def test_missing_key_is_a_client_error(self, app):
        client, _, _ = app
        response = client.get("/_components/inline-edit/pensum/edit")
        assert response.status_code == 422

    def test_several_fields_get_their_titles_as_labels(self):
        hx = WebApp()

        async def load(key: str) -> _Grad:
            return _Grad(degree=50, since=datetime.date(2026, 4, 1))

        async def save(key: str, value: _Grad) -> _Grad:
            return value

        c.InlineEdit[_Grad](
            routes=hx, name="grad", type=_Grad, label="Grad AU", load=load, save=save
        )
        html = (
            TestClient(hx.create_app())
            .get("/_components/inline-edit/grad/edit", params={"key": "x"})
            .text
        )
        assert ">Grad<input" in html
        assert ">Seit<input" in html
        assert 'type="date"' in html
        assert 'value="2026-04-01"' in html


class TestSubmit:
    URL = "/_components/headless-form/inline-edit-pensum/submit"

    def test_valid_value_is_saved_and_displayed_out_of_band(self, app):
        client, store, _ = app
        html = client.post(
            self.URL, params={"key": "case-1"}, data={"value": "80"}
        ).text
        assert store["case-1"] == 80
        assert html.startswith(
            '<div class="hx-inline-edit" id="hx-inline-edit--pensum--case-1" hx-swap-oob="outerHTML">'
        )
        assert '<span class="hx-inline-edit__value">80%</span>' in html
        assert "hx-inline-edit__form" not in html

    def test_invalid_value_keeps_the_form_with_the_error(self, app):
        client, store, _ = app
        html = client.post(
            self.URL, params={"key": "case-1"}, data={"value": "120"}
        ).text
        assert store["case-1"] == 100
        assert 'id="hx-inline-edit--pensum--case-1__form"' in html
        assert 'hx-swap-oob="morph"' in html
        assert 'aria-invalid="true"' in html
        assert "less than or equal to 100" in html
        assert 'value="120"' in html

    def test_error_raised_by_save_is_shown_at_the_field(self, app):
        client, store, _ = app
        html = client.post(
            self.URL, params={"key": "case-1"}, data={"value": "13"}
        ).text
        assert store["case-1"] == 100
        assert 'aria-invalid="true"' in html
        assert "Not allowed for this case" in html

    def test_key_round_trip_with_unsafe_characters(self, app):
        client, store, pensum = app
        assert pensum.item_id("case 2/b") == "hx-inline-edit--pensum--case_20_2_2f_b"
        edit = client.get(
            "/_components/inline-edit/pensum/edit", params={"key": "case 2/b"}
        ).text
        assert "submit?key=case+2%2Fb" in edit or "submit?key=case%202%2Fb" in edit
        html = client.post(
            self.URL, params={"key": "case 2/b"}, data={"value": "60"}
        ).text
        assert store["case 2/b"] == 60
        assert 'id="hx-inline-edit--pensum--case_20_2_2f_b"' in html

    def test_missing_key_is_rejected(self, app):
        client, store, _ = app
        response = client.post(self.URL, data={"value": "80"})
        assert response.status_code == 400
        assert store["case-1"] == 100


class TestCustomFields:
    def test_fields_callback_renders_the_controls(self):
        hx = WebApp()

        async def load(key: str) -> _Pensum:
            return _Pensum(value=50)

        async def save(key: str, value: _Pensum) -> _Pensum:
            return value

        def fields(ctx: c.FormRenderContext[_Pensum]) -> y.Node:
            return c.form_field(
                "value",
                "Prozent",
                y.input,
                type="range",
                value=str(ctx.value.value),
                error_text=ctx.visible_errors.get("value"),
            )

        c.InlineEdit[_Pensum](
            routes=hx,
            name="p",
            type=_Pensum,
            label="Pensum",
            load=load,
            save=save,
            fields=fields,
        )
        client = TestClient(hx.create_app())
        html = client.get("/_components/inline-edit/p/edit", params={"key": "x"}).text
        assert 'type="range"' in html
        assert ">Prozent<input" in html
        error = client.post(
            "/_components/headless-form/inline-edit-p/submit",
            params={"key": "x"},
            data={"value": "-1"},
        ).text
        assert 'aria-invalid="true"' in error


class TestAssets:
    def test_page_loads_the_script(self, app):
        client, _, _ = app
        assert (
            '<script src="/static/js/pyhx.inline-edit.js"></script>'
            in client.get("/").text
        )

    def test_styles_are_imported_into_the_pyhx_layer(self, app):
        client, _, _ = app
        css = client.get("/static/css/pyhx.css").text
        assert '@import "./pyhx/components/data/inline_edit.css" layer(pyhx);' in css
        assert (
            client.get("/static/css/pyhx/components/data/inline_edit.css").status_code
            == 200
        )
        assert client.get("/static/js/pyhx.inline-edit.js").status_code == 200


class TestTexts:
    def test_default_texts_follow_the_request_language(self, app):
        client, _, _ = app
        german = {"Accept-Language": "de-CH"}
        page = client.get("/", headers=german).text
        assert 'aria-label="Pensum bearbeiten"' in page
        form = client.get(
            "/_components/inline-edit/pensum/edit",
            params={"key": "case-1"},
            headers=german,
        ).text
        assert ">Speichern</button>" in form
        assert ">Abbrechen</button>" in form
        assert "Esc abbrechen · ↵ speichern" in form

    def test_texts_can_be_replaced(self):
        hx = WebApp()

        async def load(key: str) -> _Pensum:
            return _Pensum(value=50)

        async def save(key: str, value: _Pensum) -> _Pensum:
            return value

        item = c.InlineEdit[_Pensum](
            routes=hx,
            name="p",
            type=_Pensum,
            label="Pensum",
            load=load,
            save=save,
            save_label="Korrektur speichern",
            edit_label="Pensum korrigieren",
            shortcuts_hint=None,
        )

        @hx.page("/", title="Home")
        async def home() -> y.Node:
            return await item.render("x")

        client = TestClient(hx.create_app())
        assert 'aria-label="Pensum korrigieren"' in client.get("/").text
        form = client.get("/_components/inline-edit/p/edit", params={"key": "x"}).text
        assert ">Korrektur speichern</button>" in form
        assert "hx-inline-edit__shortcuts" not in form
