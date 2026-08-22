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
async def test_duplicate_slug_on_default_domain_is_rejected(client: AsyncClient):
    """Two different people, neither using a custom domain, cannot claim the same slug."""
    headers1, workspace1 = await _register_and_get_workspace(client, "slugowner1@company.com")
    headers2, workspace2 = await _register_and_get_workspace(client, "slugowner2@company.com")

    first = await client.post("/api/v1/links", json={
        "destination_url": "https://a.example.com",
        "slug": "shared-slug",
        "workspace_id": workspace1,
    }, headers=headers1)
    assert first.status_code == 201

    second = await client.post("/api/v1/links", json={
        "destination_url": "https://b.example.com",
        "slug": "shared-slug",
        "workspace_id": workspace2,
    }, headers=headers2)
    assert second.status_code == 400
    assert "already taken" in second.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_create_link_under_another_workspaces_domain(client: AsyncClient, db_session):
    from pulseroute.models.domain import CustomDomain

    _headers1, workspace1 = await _register_and_get_workspace(client, "domainowner-a@company.com")
    headers2, _workspace2 = await _register_and_get_workspace(client, "domainowner-b@company.com")

    domain = CustomDomain(workspace_id=workspace1, domain="a-owns-this.com", verification_code="x", is_verified=True)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)

    res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/hijack",
        "domain_id": domain.id,
        "workspace_id": _workspace2,
    }, headers=headers2)
    assert res.status_code == 400
    assert "Invalid or unverified" in res.json()["detail"]


@pytest.mark.asyncio
async def test_require_custom_domain_mode(client: AsyncClient, db_session):
    from pulseroute.core.config import settings
    from pulseroute.models.domain import CustomDomain

    headers, workspace_id = await _register_and_get_workspace(client, "byod-user@company.com")

    domain = CustomDomain(workspace_id=workspace_id, domain="byod-user.com", verification_code="x", is_verified=True)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)

    orig = settings.REQUIRE_CUSTOM_DOMAIN
    settings.REQUIRE_CUSTOM_DOMAIN = True
    try:
        # Anonymous link creation is fully disabled in this mode
        anon_res = await client.post("/api/v1/links", json={"destination_url": "https://example.com/anon"})
        assert anon_res.status_code == 400

        # Logged-in creation without a domain_id is also rejected
        no_domain_res = await client.post("/api/v1/links", json={
            "destination_url": "https://example.com/no-domain",
            "workspace_id": workspace_id,
        }, headers=headers)
        assert no_domain_res.status_code == 400

        # Creation against the workspace's own verified domain succeeds
        ok_res = await client.post("/api/v1/links", json={
            "destination_url": "https://example.com/ok",
            "domain_id": domain.id,
            "workspace_id": workspace_id,
        }, headers=headers)
        assert ok_res.status_code == 201
    finally:
        settings.REQUIRE_CUSTOM_DOMAIN = orig


@pytest.mark.asyncio
async def test_link_short_url_uses_its_own_custom_domain(client: AsyncClient, db_session):
    """short_url must reflect the link's actual custom domain, not whatever host the API request came in on."""
    from pulseroute.models.domain import CustomDomain

    headers, workspace_id = await _register_and_get_workspace(client, "domain-shorturl@company.com")

    domain = CustomDomain(workspace_id=workspace_id, domain="branded.example", verification_code="x", is_verified=True)
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)

    res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/target",
        "domain_id": domain.id,
        "workspace_id": workspace_id,
    }, headers=headers)
    assert res.status_code == 201
    assert res.json()["short_url"].startswith("https://branded.example/")

    list_res = await client.get(f"/api/v1/links?workspace_id={workspace_id}", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()[0]["short_url"].startswith("https://branded.example/")


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
