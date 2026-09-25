import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_and_workspace_isolation(client: AsyncClient):
    # 1. Register User 1
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "user1@company.com", "password": "SecurePassword123!", "full_name": "User One"},
    )
    assert reg1.status_code == 200

    # 2. Login User 1
    login1 = await client.post(
        "/api/v1/auth/login", json={"email": "user1@company.com", "password": "SecurePassword123!"}
    )
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
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user2@competitor.com", "password": "AnotherSecurePassword123!", "full_name": "User Two"},
    )
    login2 = await client.post(
        "/api/v1/auth/login", json={"email": "user2@competitor.com", "password": "AnotherSecurePassword123!"}
    )
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 5. User 2 tries to list User 1's workspace links -> MUST BE FORBIDDEN 403
    forbidden_list = await client.get(f"/api/v1/links?workspace_id={user1_ws_id}", headers=headers2)
    assert forbidden_list.status_code == 403

    # 6. User 1 creates a link in their own workspace
    link_res = await client.post(
        "/api/v1/links",
        json={
            "destination_url": "https://example.com/secret",
            "workspace_id": user1_ws_id,
        },
        headers=headers1,
    )
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

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "bystander@company.com", "password": "SecurePassword123!", "full_name": "Bystander"},
    )
    assert reg.status_code == 200
    login = await client.post(
        "/api/v1/auth/login", json={"email": "bystander@company.com", "password": "SecurePassword123!"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    delete_res = await client.delete(f"/api/v1/links/{link_id}", headers=headers)
    assert delete_res.status_code == 404


@pytest.mark.asyncio
async def test_workspace_deletion_restricted_to_owner(client: AsyncClient):
    # 1. Register User 1 and User 2
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "wsowner@example.com", "password": "SecurePassword123!", "full_name": "WS Owner"},
    )
    assert reg1.status_code == 200
    token1 = (
        await client.post(
            "/api/v1/auth/login", json={"email": "wsowner@example.com", "password": "SecurePassword123!"}
        )
    ).json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "wsother@example.com", "password": "SecurePassword123!", "full_name": "WS Other"},
    )
    assert reg2.status_code == 200
    token2 = (
        await client.post(
            "/api/v1/auth/login", json={"email": "wsother@example.com", "password": "SecurePassword123!"}
        )
    ).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 2. Get User 1 workspace
    workspaces1 = (await client.get("/api/v1/workspaces", headers=headers1)).json()
    ws1_id = workspaces1[0]["id"]

    # 3. Create a link inside User 1 workspace
    lnk = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/target", "workspace_id": ws1_id, "slug": "ws-del-test"},
        headers=headers1,
    )
    assert lnk.status_code == 201

    # 4. User 2 (not owner) tries to delete User 1's workspace -> MUST BE 403 Forbidden
    forbidden_delete = await client.delete(f"/api/v1/workspaces/{ws1_id}", headers=headers2)
    assert forbidden_delete.status_code == 403

    # 5. User 1 deletes their own workspace -> MUST BE 204 No Content
    owner_delete = await client.delete(f"/api/v1/workspaces/{ws1_id}", headers=headers1)
    assert owner_delete.status_code == 204

    # 6. Verify workspace and links are gone
    remaining_ws = (await client.get("/api/v1/workspaces", headers=headers1)).json()
    assert len(remaining_ws) == 0

    # Link should no longer resolve / exist
    get_link = await client.get("/ws-del-test", follow_redirects=False)
    assert get_link.status_code == 404


@pytest.mark.asyncio
async def test_account_deletion_kvkk_gdpr_flow(client: AsyncClient):
    # 1. Register account
    email = "delete-me@example.com"
    password = "SuperPassword123!"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Doomed User"},
    )
    assert reg.status_code == 200

    token = (
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. User has a default workspace and creates a short link
    workspaces = (await client.get("/api/v1/workspaces", headers=headers)).json()
    ws_id = workspaces[0]["id"]

    lnk = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/erasure", "workspace_id": ws_id, "slug": "erasure-link"},
        headers=headers,
    )
    assert lnk.status_code == 201

    # 3. Fail: Invalid confirmation text
    res_bad_conf = await client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={"password": password, "confirmation": "NO"},
        headers=headers,
    )
    assert res_bad_conf.status_code == 400

    # 4. Fail: Incorrect password
    res_wrong_pw = await client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={"password": "WrongPassword!", "confirmation": "DELETE"},
        headers=headers,
    )
    assert res_wrong_pw.status_code == 401

    # 5. Success: Valid password and confirmation
    res_del = await client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={"password": password, "confirmation": "DELETE"},
        headers=headers,
    )
    assert res_del.status_code == 200
    assert "KVKK / GDPR" in res_del.json()["detail"]

    # 6. Verify user is completely erased (login fails)
    relogin = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert relogin.status_code == 401

    # 7. Old Bearer token is rejected because user no longer exists
    profile = await client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 401

    # 8. Link is completely erased and purged
    redir = await client.get("/erasure-link", follow_redirects=False)
    assert redir.status_code == 404

