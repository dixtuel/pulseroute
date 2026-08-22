import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_domain_onboarding_and_dns_instructions(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "domainowner@company.com",
        "password": "SecurePassword123!",
        "full_name": "Domain Owner",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "domainowner@company.com", "password": "SecurePassword123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]

    # Unauthenticated domain creation is rejected
    anon_res = await client.post("/api/v1/domains", json={"domain": "links.mybrand.com", "workspace_id": workspace_id})
    assert anon_res.status_code == 401

    # 1. Add custom domain
    res = await client.post("/api/v1/domains", json={
        "domain": "links.mybrand.com",
        "workspace_id": workspace_id,
        "custom_not_found_url": "https://mybrand.com/404"
    }, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["domain"] == "links.mybrand.com"
    assert data["is_verified"] is False
    assert "dns_instructions" in data
    assert data["dns_instructions"]["type"] == "CNAME"
    assert data["dns_instructions"]["name"] == "links"

    domain_id = data["id"]

    # 2. List domains (workspace-scoped, auth required)
    list_res = await client.get(f"/api/v1/domains?workspace_id={workspace_id}", headers=headers)
    assert list_res.status_code == 200
    domains = list_res.json()
    assert len(domains) >= 1

    # 3. Test verification check (pending status when DNS is not yet live)
    verify_res = await client.post(f"/api/v1/domains/{domain_id}/verify", headers=headers)
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert "status" in verify_data
    assert "dns_instructions" in verify_data


@pytest.mark.asyncio
async def test_custom_domains_can_be_disabled_server_wide(client: AsyncClient):
    from pulseroute.core.config import settings

    await client.post("/api/v1/auth/register", json={
        "email": "domaindisabled@company.com",
        "password": "SecurePassword123!",
        "full_name": "Domain Disabled",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "domaindisabled@company.com", "password": "SecurePassword123!"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]

    orig = settings.ALLOW_CUSTOM_DOMAINS
    settings.ALLOW_CUSTOM_DOMAINS = False
    try:
        res = await client.post("/api/v1/domains", json={
            "domain": "blocked.example.com", "workspace_id": workspace_id
        }, headers=headers)
        assert res.status_code == 403
    finally:
        settings.ALLOW_CUSTOM_DOMAINS = orig
