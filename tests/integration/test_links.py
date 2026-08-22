import pytest
from httpx import AsyncClient


async def _register_and_get_workspace(client: AsyncClient, email: str) -> tuple[dict, int]:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Test User",
    })
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]
    return headers, workspace_id


@pytest.mark.asyncio
async def test_create_and_get_link(client: AsyncClient):
    headers, workspace_id = await _register_and_get_workspace(client, "linkuser@company.com")

    payload = {
        "destination_url": "https://github.com/dixtuel",
        "slug": "dixtuel-gh",
        "title": "Asrin Github Profile",
        "tags": "dev,github",
        "public_stats": True,
        "workspace_id": workspace_id,
    }
    response = await client.post("/api/v1/links", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "dixtuel-gh"
    assert data["destination_url"] == "https://github.com/dixtuel"
    assert data["tags"] == "dev,github"
    assert data["public_stats"] is True

    # List links with search (workspace-scoped, auth required)
    list_res = await client.get(f"/api/v1/links?workspace_id={workspace_id}&search=dixtuel", headers=headers)
    assert list_res.status_code == 200
    links = list_res.json()
    assert len(links) >= 1

    # List links with tag filter
    tag_res = await client.get(f"/api/v1/links?workspace_id={workspace_id}&tag=github", headers=headers)
    assert tag_res.status_code == 200
    tag_links = tag_res.json()
    assert len(tag_links) >= 1

    # Unauthenticated listing is rejected
    anon_list_res = await client.get(f"/api/v1/links?workspace_id={workspace_id}")
    assert anon_list_res.status_code == 401

    # Update link (PATCH)
    link_id = data["id"]
    patch_res = await client.patch(f"/api/v1/links/{link_id}", json={
        "title": "Updated Title",
        "tags": "updated,tag"
    }, headers=headers)
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["title"] == "Updated Title"
    assert patched_data["tags"] == "updated,tag"


@pytest.mark.asyncio
async def test_anonymous_link_creation_and_count(client: AsyncClient):
    payload = {"destination_url": "https://example.com/anon"}
    response = await client.post("/api/v1/links", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None

    # Anonymous links cannot be edited or deleted via the API (no owner)
    patch_res = await client.patch(f"/api/v1/links/{data['id']}", json={"title": "x"})
    assert patch_res.status_code == 401  # no auth at all

    count_res = await client.get("/api/v1/links/stats/anonymous-count")
    assert count_res.status_code == 200
    assert count_res.json()["count"] >= 1


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
