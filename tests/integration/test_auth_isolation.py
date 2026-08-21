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

    # 5. User 2 tries to generate an API key on User 1's workspace -> MUST BE FORBIDDEN 403
    forbidden_attempt = await client.post(
        f"/api/v1/workspaces/{user1_ws_id}/api-keys",
        headers=headers2
    )
    assert forbidden_attempt.status_code == 403

    # 6. User 1 generates API key on own workspace -> 200 OK
    api_key_res = await client.post(
        f"/api/v1/workspaces/{user1_ws_id}/api-keys",
        headers=headers1
    )
    assert api_key_res.status_code == 200
    raw_api_key = api_key_res.json()["api_key"]
    assert raw_api_key.startswith("pr_live_")

    # 7. Authenticate via raw API key
    api_key_headers = {"Authorization": f"Bearer {raw_api_key}"}
    ws_via_api_key = await client.get("/api/v1/workspaces", headers=api_key_headers)
    assert ws_via_api_key.status_code == 200
