from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_redirect_flow(client: AsyncClient):
    # 1. Create link
    create_res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/target-page",
        "slug": "ex-target",
        "public_stats": True
    })
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
async def test_redirect_expired_fallback(client: AsyncClient):
    # Create expired link with fallback url
    create_res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/active-sale",
        "slug": "flash-sale",
        "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "expired_url": "https://example.com/campaign-ended"
    })
    assert create_res.status_code == 201

    redirect_res = await client.get("/flash-sale", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://example.com/campaign-ended"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    res = await client.get("/non-existent-slug-xyz", follow_redirects=False)
    assert res.status_code == 404
