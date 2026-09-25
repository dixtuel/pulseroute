import re
import time
from datetime import UTC, datetime, timedelta

import orjson
import pytest
from httpx import AsyncClient

from pulseroute.common.redirect_ticket import issue_ticket


def _start_ticket(html: str) -> str:
    match = re.search(r"const startTicket = (\"[^\"]+\");", html)
    assert match is not None
    return orjson.loads(match.group(1))


@pytest.mark.asyncio
async def test_redirect_flow(client: AsyncClient):
    # 1. Create link
    create_res = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/target-page", "slug": "ex-target", "public_stats": True},
    )
    assert create_res.status_code == 201

    # 2. Test redirect
    redirect_res = await client.get("/ex-target", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://example.com/target-page"
    assert "no-store" in redirect_res.headers["cache-control"]

    # 3. Test Dub.co style public stats /ex-target+
    stats_res = await client.get("/ex-target+")
    assert stats_res.status_code == 200
    stats_json = stats_res.json()
    assert "total_clicks" in stats_json


@pytest.mark.asyncio
async def test_redirect_interstitial_page_with_adsense(client: AsyncClient):
    """
    AdSense is a single, server-administrator-controlled account (GLOBAL_ADSENSE_*),
    never something an individual user/link can set -- Google AdSense requires per-site
    ownership verification, so per-user monetization isn't offered at all.
    """
    from pulseroute.core.config import settings

    orig_client, orig_slot = settings.GLOBAL_ADSENSE_CLIENT_ID, settings.GLOBAL_ADSENSE_SLOT_ID
    settings.GLOBAL_ADSENSE_CLIENT_ID = "ca-pub-1234567890"
    settings.GLOBAL_ADSENSE_SLOT_ID = "9876543210"
    try:
        # The browser countdown is platform-controlled, regardless of legacy fields.
        create_res = await client.post(
            "/api/v1/links",
            json={
                "destination_url": "https://example.com/sponsored-target",
                "slug": "ad-link",
                "interstitial_delay": 5,
                "interstitial_title": "Please wait for sponsor",
            },
        )
        assert create_res.status_code == 201

        # Browser request with text/html -> Returns Interstitial HTML with the platform's AdSense tags
        browser_res = await client.get("/ad-link", headers={"Accept": "text/html"})
        assert browser_res.status_code == 200
        assert "ca-pub-1234567890" in browser_res.text
        assert "9876543210" in browser_res.text
        assert "adsbygoogle" in browser_res.text
        assert "interstitialDelay" not in browser_res.text
    finally:
        settings.GLOBAL_ADSENSE_CLIENT_ID = orig_client
        settings.GLOBAL_ADSENSE_SLOT_ID = orig_slot


@pytest.mark.asyncio
async def test_redirect_expired_fallback(client: AsyncClient):
    # Create expired link with fallback url
    create_res = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com/active-sale",
            "slug": "flash-sale",
            "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "expired_url": "https://example.com/campaign-ended",
        },
    )
    assert create_res.status_code == 201

    redirect_res = await client.get("/flash-sale", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://example.com/campaign-ended"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    res = await client.get("/non-existent-slug-xyz", follow_redirects=False)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_browser_shell_does_not_contact_backends(client: AsyncClient, monkeypatch):
    def unexpected_db():
        raise AssertionError("browser shell contacted the database")

    monkeypatch.setattr("pulseroute.api.redirect.async_session_maker", unexpected_db)
    response = await client.get("/any-slug", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "Bağlantı kontrol ediliyor" in response.text
    assert "no-store" in response.headers["cache-control"]


@pytest.mark.asyncio
async def test_browser_link_validation_and_minimum_wait(client: AsyncClient):
    created = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/verified", "slug": "wait-five", "interstitial_delay": 0},
    )
    assert created.status_code == 201
    assert "interstitial_delay" not in created.json()

    shell = await client.get("/wait-five", headers={"Accept": "text/html"})
    ticket = _start_ticket(shell.text)
    checked = await client.get(f"/api/v1/redirect/resolve/wait-five?ticket={ticket}")
    assert checked.status_code == 200
    assert 0 < checked.json()["wait_ms"] <= 5000
    assert "target_url" not in checked.json()

    early = await client.post("/api/v1/redirect/complete", json={"ticket": checked.json()["ticket"]})
    assert early.status_code == 425


@pytest.mark.asyncio
async def test_browser_long_validation_skips_countdown(client: AsyncClient):
    created = await client.post(
        "/api/v1/links", json={"destination_url": "https://example.com/slow", "slug": "slow-check"}
    )
    assert created.status_code == 201
    ticket = issue_ticket(
        {"kind": "start", "host": "testserver", "slug": "slow-check", "started_at": time.time() - 6}
    )
    checked = await client.get(f"/api/v1/redirect/resolve/slow-check?ticket={ticket}")
    assert checked.status_code == 200
    assert checked.json()["wait_ms"] == 0
    completed = await client.post("/api/v1/redirect/complete", json={"ticket": checked.json()["ticket"]})
    assert completed.status_code == 200
    assert completed.json()["target_url"] == "https://example.com/slow"


@pytest.mark.asyncio
async def test_browser_missing_link_returns_not_found_after_shell(client: AsyncClient):
    shell = await client.get("/92837272", headers={"Accept": "text/html"})
    assert shell.status_code == 200
    ticket = _start_ticket(shell.text)
    result = await client.get(f"/api/v1/redirect/resolve/92837272?ticket={ticket}")
    assert result.status_code == 404
    assert result.json()["detail"] == "Link not found"
