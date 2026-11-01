"""The language flows of ``samples/user_auth``: anonymous visitors, signed-in users, overrides."""

import pytest
from fastapi.testclient import TestClient

from samples.user_auth import main as sample

PASSWORD_SUBMIT_URL = "/_components/data-form/app-login/submit"


@pytest.fixture(autouse=True)
def reset_languages():
    """The sample's users live as long as the module; start every test without stored languages."""
    yield
    for username, locale in (("jane", None), ("marco", "it")):
        user = sample.users.get_user_by_username(username)
        user.locale = locale
        sample.users.upsert_user(user)


def browser(accept_language: str | None = None) -> TestClient:
    client = TestClient(sample.app, follow_redirects=False)
    if accept_language:
        client.headers["Accept-Language"] = accept_language
    return client


def sign_in(client: TestClient, username: str) -> None:
    response = client.post(
        PASSWORD_SUBMIT_URL, data={"username": username, "password": "pw", "next": ""}
    )
    assert response.headers.get("HX-Redirect") == "/"


def switch(client: TestClient, locale: str, **headers: str):
    return client.post(
        "/_pyhx/locale", data={"locale": locale, "next": "/"}, headers=headers
    )


class TestAnonymous:
    def test_english_by_default(self):
        page = browser().get("/").text

        assert "User authentication sample" in page and '<html lang="en"' in page

    def test_browser_language(self):
        page = browser("de-CH, fr;q=0.5").get("/").text

        assert (
            "Beispiel: Benutzeranmeldung" in page
            and "Sie sind nicht angemeldet." in page
        )

    def test_switch_is_kept_in_the_session_only(self):
        client = browser()

        assert switch(client, "fr").headers["location"] == "/"

        assert "Exemple : connexion des utilisateurs" in client.get("/").text
        assert "User authentication sample" in browser().get("/").text

    def test_switcher_is_on_the_page(self):
        page = browser().get("/").text

        assert all(
            name in page for name in ("English", "Deutsch", "Italiano", "Français")
        )


class TestSignedIn:
    def test_switch_is_stored_on_the_user_and_back_after_signing_in_again(self):
        client = browser()
        sign_in(client, "jane")

        switch(client, "de")

        assert sample.users.get_user_by_username("jane").locale == "de"
        fresh = browser()
        sign_in(fresh, "jane")
        assert "Angemeldet als <strong>Jane Doe</strong>." in fresh.get("/").text

    def test_stored_language_without_choosing(self):
        client = browser("de")
        sign_in(client, "marco")

        page = client.get("/protected").text

        assert (
            "Hai effettuato l&#39;accesso come <strong>Marco Rossi</strong>." in page
            or ("Hai effettuato l'accesso come <strong>Marco Rossi</strong>." in page)
        )

    def test_session_beats_the_stored_language(self):
        client = browser()
        switch(client, "fr")
        sign_in(client, "marco")

        assert (
            "Connecté en tant que <strong>Marco Rossi</strong>." in client.get("/").text
        )
        assert sample.users.get_user_by_username("marco").locale == "it"

    def test_htmx_switch_reloads_the_page(self):
        client = browser()
        sign_in(client, "jane")

        response = switch(client, "it", **{"HX-Request": "true"})

        assert response.headers["HX-Refresh"] == "true"


class TestTextsAndFormatting:
    def test_plural_and_numbers(self):
        page = browser("de").get("/").text

        assert "Es gibt 3 offene Fälle im Wert von 99.247,25." in page
        assert "1.234,50\xa0€" in page

    def test_relative_times_and_dates(self):
        page = browser("it").get("/").text

        assert "3 ore fa" in page and "5 minuti fa" in page

    def test_the_sample_overrides_a_pyhx_text_and_falls_back_to_pyhx_for_the_rest(self):
        client = browser()
        switch(client, "de")

        login = client.get("/login").text

        assert "Einloggen" in login  # the sample's catalog overrides pyhx's "Anmelden"
        assert "Passwort" in login  # from pyhx's own catalog
