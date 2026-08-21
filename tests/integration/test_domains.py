import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_domain_onboarding_and_dns_instructions(client: AsyncClient):
    # 1. Add custom domain
    res = await client.post("/api/v1/domains", json={
        "domain": "links.mybrand.com",
        "custom_not_found_url": "https://mybrand.com/404"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["domain"] == "links.mybrand.com"
    assert data["is_verified"] is False
    assert "dns_instructions" in data
    assert data["dns_instructions"]["type"] == "CNAME"
    assert data["dns_instructions"]["name"] == "links"

    domain_id = data["id"]

    # 2. List domains
    list_res = await client.get("/api/v1/domains")
    assert list_res.status_code == 200
    domains = list_res.json()
    assert len(domains) >= 1

    # 3. Test verification check (pending status when DNS is not yet live)
    verify_res = await client.post(f"/api/v1/domains/{domain_id}/verify")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert "status" in verify_data
    assert "dns_instructions" in verify_data
