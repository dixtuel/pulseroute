import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_redirect_flow(client: AsyncClient):
    # 1. Create link
    create_res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/target-page",
        "slug": "ex-target"
    })
    assert create_res.status_code == 201

    # 2. Test redirect
    redirect_res = await client.get("/ex-target", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://example.com/target-page"
    assert "no-store" in redirect_res.headers["cache-control"]


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    res = await client.get("/non-existent-slug-xyz", follow_redirects=False)
    assert res.status_code == 404
