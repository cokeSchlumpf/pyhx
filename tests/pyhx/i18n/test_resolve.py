import asyncio
from dataclasses import dataclass

import htpy as y
import httpx
import pytest
from commons.users import AnonymousUser
from fastapi.testclient import TestClient
from starlette.requests import Request

from pyhx.core.primitives import negotiate_locale
from pyhx.core.primitives.negotiate_locale import (
    LocaleSettings,
    match_locale,
    parse_accept_language,
    resolve_locale,
    use_locale,
)
from pyhx.core.request_context import RequestContext
from pyhx.core.webapp import WebApp


@dataclass
class _User:
    locale: str | None


def _context(
    *, session: dict | None = None, user=None, accept_language: str | None = None
) -> RequestContext:
    headers = (
        [(b"accept-language", accept_language.encode())]
        if accept_language is not None
        else []
    )
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "query_string": b"",
    }
    if session is not None:
        scope["session"] = session
    return RequestContext(request=Request(scope), user=user or AnonymousUser())


class TestMatchLocale:
    @pytest.mark.parametrize(
        ("candidate", "expected"),
        [
            ("de", "de"),
            ("DE", "de"),
            ("de-CH", "de"),
            ("de_CH", "de"),
            ("es", None),
            ("", None),
            (None, None),
        ],
    )
    def test_matches_offered_languages(self, candidate, expected):
        assert match_locale(candidate, ["en", "de"]) == expected

    def test_exact_regional_entry_wins(self):
        assert match_locale("de-CH", ["de", "de-CH"]) == "de-CH"


class TestParseAcceptLanguage:
    def test_orders_by_weight_and_keeps_header_order(self):
        assert parse_accept_language("en;q=0.5, fr, de-CH;q=0.9, it") == [
            "fr",
            "it",
            "de-CH",
            "en",
        ]

    def test_drops_star_zero_weight_and_garbage(self):
        assert parse_accept_language("*, es;q=0, de;q=abc, , en") == ["en"]


class TestResolveLocale:
    def test_session_beats_user_and_browser(self):
        ctx = _context(
            session={"pyhx.locale": "fr"}, user=_User("it"), accept_language="de"
        )
        assert resolve_locale(ctx) == "fr"

    def test_user_beats_browser(self):
        assert (
            resolve_locale(_context(session={}, user=_User("it"), accept_language="de"))
            == "it"
        )

    def test_browser_by_weight(self):
        assert (
            resolve_locale(_context(accept_language="es, de;q=0.5, fr;q=0.8")) == "fr"
        )

    def test_values_not_offered_are_skipped(self):
        ctx = _context(
            session={"pyhx.locale": "es"}, user=_User("pt"), accept_language="nl, de-AT"
        )
        assert resolve_locale(ctx) == "de"

    def test_none_without_a_match(self):
        assert resolve_locale(_context(accept_language="es")) is None

    def test_user_argument_replaces_the_user_of_the_request(self):
        ctx = _context(session={}, user=_User("it"), accept_language="de")
        assert resolve_locale(ctx, user=_User("fr")) == "fr"

    def test_without_a_request_only_the_user_counts(self):
        assert resolve_locale(None, user=_User("it")) == "it"


class TestNegotiateLocale:
    def test_default_outside_a_request(self):
        assert negotiate_locale() == "en"
        assert negotiate_locale(fallback="de") == "de"

    def test_default_when_nothing_matches(self, locale_settings, set_context):
        set_context(_context(accept_language="es"))
        assert negotiate_locale() == "en"
        assert negotiate_locale(fallback="fr") == "fr"

    def test_resolved_once_per_request(self, monkeypatch, set_context):
        calls = []
        settings = LocaleSettings(supported_locales=["en", "de"])
        monkeypatch.setattr(
            LocaleSettings, "read", staticmethod(lambda: calls.append(1) or settings)
        )
        set_context(_context(accept_language="de"))

        assert [negotiate_locale() for _ in range(5)] == ["de"] * 5
        assert len(calls) == 1

    def test_use_locale_wins_and_is_reset(self, set_context):
        set_context(_context(accept_language="de"))
        with use_locale("it"):
            assert negotiate_locale() == "it"
            with use_locale("es"):
                assert negotiate_locale() == "en"
        assert negotiate_locale() == "de"


class TestInRequests:
    def test_html_lang_is_the_request_language(self):
        hx = WebApp()

        @hx.page("/", title="Home")
        async def home() -> y.Node:
            return y.p["hi"]

        response = TestClient(hx.create_app()).get(
            "/", headers={"Accept-Language": "fr-CH,fr;q=0.9"}
        )

        assert '<html lang="fr"' in response.text

    def test_concurrent_requests_keep_their_language(self):
        hx = WebApp()

        @hx.fragment.get("/probe")
        async def probe() -> y.Node:
            first = negotiate_locale()
            await asyncio.sleep(0.05)
            return y.span[f"{first}:{negotiate_locale()}"]

        async def run() -> list[str]:
            transport = httpx.ASGITransport(app=hx.create_app())
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                responses = await asyncio.gather(
                    *(
                        client.get("/probe", headers={"Accept-Language": lang})
                        for lang in ["de", "fr", "it", "en"] * 3
                    )
                )
            return [r.text for r in responses]

        texts = asyncio.run(run())

        for lang, text in zip(["de", "fr", "it", "en"] * 3, texts, strict=True):
            assert f"{lang}:{lang}" in text
