import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_link(client: AsyncClient):
    payload = {
        "destination_url": "https://github.com/dixtuel",
        "slug": "dixtuel-gh",
        "title": "Asrin Github Profile",
        "tags": "dev,github",
        "public_stats": True,
    }
    response = await client.post("/api/v1/links", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "dixtuel-gh"
    assert data["destination_url"] == "https://github.com/dixtuel"
    assert data["tags"] == "dev,github"
    assert data["public_stats"] is True

    # List links with search
    list_res = await client.get("/api/v1/links?search=dixtuel")
    assert list_res.status_code == 200
    links = list_res.json()
    assert len(links) >= 1

    # List links with tag filter
    tag_res = await client.get("/api/v1/links?tag=github")
    assert tag_res.status_code == 200
    tag_links = tag_res.json()
    assert len(tag_links) >= 1

    # Update link (PATCH)
    link_id = data["id"]
    patch_res = await client.patch(f"/api/v1/links/{link_id}", json={
        "title": "Updated Title",
        "tags": "updated,tag"
    })
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["title"] == "Updated Title"
    assert patched_data["tags"] == "updated,tag"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
