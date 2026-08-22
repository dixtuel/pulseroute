import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_and_workspace_isolation(client: AsyncClient):
    # 1. Register User 1
    reg1 = await client.post("/api/v1/auth/register", json={
        "email": "user1@company.com",
        "password": "SecurePassword123!",
        "full_name": "User One"
    })
    assert reg1.status_code == 200

    # 2. Login User 1
    login1 = await client.post("/api/v1/auth/login", json={
        "email": "user1@company.com",
        "password": "SecurePassword123!"
    })
    assert login1.status_code == 200
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 3. List User 1's workspaces (should have personal workspace)
    ws1 = await client.get("/api/v1/workspaces", headers=headers1)
    assert ws1.status_code == 200
    workspaces1 = ws1.json()
    assert len(workspaces1) == 1
    user1_ws_id = workspaces1[0]["id"]

    # 4. Register & Login User 2
    await client.post("/api/v1/auth/register", json={
        "email": "user2@competitor.com",
        "password": "AnotherSecurePassword123!",
        "full_name": "User Two"
    })
    login2 = await client.post("/api/v1/auth/login", json={
        "email": "user2@competitor.com",
        "password": "AnotherSecurePassword123!"
    })
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 5. User 2 tries to list User 1's workspace links -> MUST BE FORBIDDEN 403
    forbidden_list = await client.get(f"/api/v1/links?workspace_id={user1_ws_id}", headers=headers2)
    assert forbidden_list.status_code == 403

    # 6. User 1 creates a link in their own workspace
    link_res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/secret",
        "workspace_id": user1_ws_id,
    }, headers=headers1)
    assert link_res.status_code == 201
    link_id = link_res.json()["id"]

    # 7. User 2 cannot see, edit, or delete User 1's link
    forbidden_patch = await client.patch(f"/api/v1/links/{link_id}", json={"title": "hijacked"}, headers=headers2)
    assert forbidden_patch.status_code == 403

    forbidden_delete = await client.delete(f"/api/v1/links/{link_id}", headers=headers2)
    assert forbidden_delete.status_code == 403

    forbidden_analytics = await client.get(
        f"/api/v1/analytics?workspace_id={user1_ws_id}&link_id={link_id}", headers=headers2
    )
    assert forbidden_analytics.status_code == 403

    # 8. User 1 can manage their own link
    own_patch = await client.patch(f"/api/v1/links/{link_id}", json={"title": "owned"}, headers=headers1)
    assert own_patch.status_code == 200

    own_analytics = await client.get(
        f"/api/v1/analytics?workspace_id={user1_ws_id}&link_id={link_id}", headers=headers1
    )
    assert own_analytics.status_code == 200


@pytest.mark.asyncio
async def test_anonymous_links_have_no_owner_and_cannot_be_managed(client: AsyncClient):
    anon_res = await client.post("/api/v1/links", json={"destination_url": "https://example.com/anon"})
    assert anon_res.status_code == 201
    link_id = anon_res.json()["id"]

    reg = await client.post("/api/v1/auth/register", json={
        "email": "bystander@company.com",
        "password": "SecurePassword123!",
        "full_name": "Bystander"
    })
    assert reg.status_code == 200
    login = await client.post("/api/v1/auth/login", json={
        "email": "bystander@company.com", "password": "SecurePassword123!"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    delete_res = await client.delete(f"/api/v1/links/{link_id}", headers=headers)
    assert delete_res.status_code == 404
