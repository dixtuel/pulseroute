import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_webhook_lifecycle(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "webhookowner@company.com",
        "password": "SecurePassword123!",
        "full_name": "Webhook Owner",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "webhookowner@company.com", "password": "SecurePassword123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]

    # Unauthenticated webhook creation is rejected
    anon_res = await client.post("/api/v1/webhooks", json={
        "workspace_id": workspace_id, "url": "https://example.com/hook"
    })
    assert anon_res.status_code == 401

    # 1. Create webhook — secret is only ever returned here
    res = await client.post("/api/v1/webhooks", json={
        "workspace_id": workspace_id,
        "url": "https://example.com/hook",
        "events": "link.created,link.clicked",
    }, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["url"] == "https://example.com/hook"
    assert len(data["secret_key"]) == 64
    webhook_id = data["id"]

    # 2. List webhooks — secret is never exposed again
    list_res = await client.get(f"/api/v1/webhooks?workspace_id={workspace_id}", headers=headers)
    assert list_res.status_code == 200
    webhooks = list_res.json()
    assert len(webhooks) == 1
    assert "secret_key" not in webhooks[0]

    # 3. Delete webhook
    del_res = await client.delete(f"/api/v1/webhooks/{webhook_id}", headers=headers)
    assert del_res.status_code == 204

    list_res_2 = await client.get(f"/api/v1/webhooks?workspace_id={workspace_id}", headers=headers)
    assert list_res_2.json() == []


@pytest.mark.asyncio
async def test_link_creation_dispatches_webhook(client: AsyncClient, monkeypatch):
    dispatched = []

    async def fake_dispatch_event(url, secret_key, event_type, payload):
        dispatched.append((url, event_type, payload))
        return True

    from pulseroute.services import webhook_service
    monkeypatch.setattr(webhook_service.WebhookService, "dispatch_event", staticmethod(fake_dispatch_event))

    await client.post("/api/v1/auth/register", json={
        "email": "webhookfire@company.com",
        "password": "SecurePassword123!",
        "full_name": "Webhook Fire",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "webhookfire@company.com", "password": "SecurePassword123!"
    })
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]

    await client.post("/api/v1/webhooks", json={
        "workspace_id": workspace_id, "url": "https://example.com/hook", "events": "link.created"
    }, headers=headers)

    res = await client.post("/api/v1/links", json={
        "destination_url": "https://example.com/target",
        "workspace_id": workspace_id,
    }, headers=headers)
    assert res.status_code == 201

    import asyncio
    await asyncio.sleep(0.05)  # let the fire-and-forget task run

    assert len(dispatched) == 1
    assert dispatched[0][1] == "link.created"
    assert dispatched[0][2]["destination_url"] == "https://example.com/target"
