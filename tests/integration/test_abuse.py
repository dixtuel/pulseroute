import re

import orjson
import pytest
from httpx import AsyncClient


def _start_ticket(html: str) -> str:
    match = re.search(r"const startTicket = (\"[^\"]+\");", html)
    assert match is not None
    return orjson.loads(match.group(1))


async def _register_and_create_link(client: AsyncClient, email: str, slug: str, dest: str) -> tuple[dict, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Abuse Test User",
        },
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    workspace_id = ws_res.json()[0]["id"]

    create_res = await client.post(
        "/api/v1/links",
        json={
            "destination_url": dest,
            "slug": slug,
            "workspace_id": workspace_id,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    return headers, slug


@pytest.mark.asyncio
async def test_abuse_report_triggers_instant_quarantine(client: AsyncClient):
    _, slug = await _register_and_create_link(
        client, "target1@victim.com", "phish-test-1", "https://innocent-looking-site.com"
    )

    # 1. Report link as phishing
    report_res = await client.post(
        "/api/v1/abuse/report",
        json={
            "short_url_or_slug": f"https://sely.tr/{slug}",
            "reason": "phishing",
            "reporter_email": "security-analyst@cert.gov.tr",
            "details": "Clone of bank login page detected.",
        },
    )
    assert report_res.status_code == 202
    data = report_res.json()
    assert data["status"] == "quarantined"
    assert "karanti" in data["message"].lower() or "quarantine" in data["action_taken"].lower()

    # 2. Direct API redirect resolution returns HTTP 451
    resolve_res = await client.get(f"/{slug}", headers={"Accept": "application/json"})
    assert resolve_res.status_code == 451
    assert "quarantined" in resolve_res.json()["detail"].lower()

    # 3. Browser verification AJAX call returns HTTP 451
    shell = await client.get(f"/{slug}", headers={"Accept": "text/html"})
    assert shell.status_code == 200
    assert "Kötüye Kullanım" in shell.text or "Şüpheli Bağlantı" in shell.text
    ticket = _start_ticket(shell.text)
    ajax_res = await client.get(f"/api/v1/redirect/resolve/{slug}?ticket={ticket}")
    assert ajax_res.status_code == 451
    assert "quarantined" in ajax_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_abuse_report_malware_triggers_quarantine(client: AsyncClient):
    _, slug = await _register_and_create_link(
        client, "target2@victim.com", "malware-test-2", "https://goodsite.org/info"
    )

    report_res = await client.post(
        "/api/v1/abuse/report",
        json={
            "short_url_or_slug": slug,
            "reason": "malware",
            "reporter_email": "threat-intel@antivirus.com",
            "details": "Dropper payload served to visitors.",
        },
    )
    assert report_res.status_code == 202
    assert report_res.json()["status"] == "quarantined"

    # Redirection is blocked
    check_res = await client.get(f"/{slug}", headers={"Accept": "application/json"})
    assert check_res.status_code == 451


@pytest.mark.asyncio
async def test_abuse_report_nonexistent_link_returns_404(client: AsyncClient):
    report_res = await client.post(
        "/api/v1/abuse/report",
        json={
            "short_url_or_slug": "non-existent-slug-xyz-999",
            "reason": "phishing",
            "reporter_email": "reporter@example.com",
        },
    )
    assert report_res.status_code == 404
    assert "not found" in report_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_abuse_web_page_renders_successfully(client: AsyncClient):
    res = await client.get("/abuse?slug=sample-slug")
    assert res.status_code == 200
    assert "Kötüye Kullanım" in res.text
    assert "sample-slug" in res.text
