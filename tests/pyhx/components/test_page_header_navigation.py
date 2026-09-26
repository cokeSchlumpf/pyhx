"""Tests for the page header's optional secondary navigation."""

import htpy as y

from pyhx.components.layouts import page_header
from pyhx.core.primitives import htmx


def test_page_header_renders_secondary_navigation():
    html = str(
        page_header(
            title=y.h1["Value Chain"],
            navigation=page_header.navigation(
                page_header.nav_item(
                    "Overview",
                    href="/value-chain",
                    active=True,
                ),
                page_header.nav_item(
                    "Hotspots",
                    href="/value-chain/hotspots",
                ),
                aria_label="Value Chain views",
            ),
        )
    )

    assert 'class="hx-page-header__navigation"' in html
    assert 'aria-label="Value Chain views"' in html
    assert 'href="/value-chain"' in html
    assert 'href="/value-chain/hotspots"' in html
    assert html.count('aria-current="page"') == 1


def test_page_header_omits_navigation_when_not_configured():
    html = str(
        page_header(
            title=y.h1["Page without navigation"],
        )
    )

    assert "hx-page-header__navigation" not in html
    assert "hx-page-header__navigation-list" not in html


def test_nav_item_forwards_htmx_attributes():
    html = str(
        page_header.nav_item(
            "Overview",
            href="/value-chain",
            **htmx(
                hx_get="/value-chain",
                hx_target="#value-chain-content",
                hx_swap="innerHTML",
                hx_push_url=True,
            ),
        )
    )

    assert 'hx-get="/value-chain"' in html
    assert 'hx-target="#value-chain-content"' in html
    assert 'hx-swap="innerHTML"' in html
    assert 'hx-push-url="true"' in html