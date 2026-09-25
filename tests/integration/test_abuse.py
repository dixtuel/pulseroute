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
    assert "kötüye kullanım" in res.text.lower() or "report abuse" in res.text.lower()
    assert "sample-slug" in res.text


@pytest.mark.asyncio
async def test_abuse_threshold_quarantine_and_auto_delete(client: AsyncClient):
    _, slug = await _register_and_create_link(
        client, "threshold_user@domain.com", "thresh-slug-1", "https://suspicious-threshold.com"
    )

    # Unique browser signals count as separate reporters; duplicate reports are deduplicated.
    async def report(number: int):
        return await client.post(
            "/api/v1/abuse/report",
            headers={"User-Agent": f"reporter-{number}"},
            json={"short_url_or_slug": slug, "reason": "spam", "reporter_email": f"r{number}@test.com"},
        )

    # The first four distinct reports are queued for review.
    r1 = await report(1)
    assert r1.status_code == 202
    assert r1.json()["status"] == "received"

    # Link is still active
    check1 = await client.get(f"/{slug}", headers={"Accept": "application/json"})
    assert check1.status_code in [200, 307]

    # 2. A second identical report is ignored and does not change the cumulative count.
    duplicate = await client.post(
        "/api/v1/abuse/report",
        headers={"User-Agent": "reporter-1"},
        json={"short_url_or_slug": slug, "reason": "spam", "reporter_email": "same-user@test.com"},
    )
    assert duplicate.status_code == 202
    assert duplicate.json()["status"] == "duplicate"

    for number in range(2, 5):
        response = await report(number)
        assert response.status_code == 202
        assert response.json()["status"] == "received"

    # Fifth distinct report reaches the quarantine threshold.
    r5 = await report(5)
    assert r5.status_code == 202
    assert r5.json()["status"] == "quarantined"

    # Redirection now returns 451
    check2 = await client.get(f"/{slug}", headers={"Accept": "application/json"})
    assert check2.status_code == 451

    # Reports six through nine remain quarantined while awaiting formal review.
    for number in range(6, 10):
        response = await report(number)
        assert response.status_code == 202
        assert response.json()["status"] == "quarantined"

    # Tenth distinct report reaches the permanent deletion threshold.
    r10 = await report(10)
    assert r10.status_code == 202
    assert r10.json()["status"] in ["deleted", "removed"]

    # Now the link is deleted/removed -> 404 or 410
    check10 = await client.get(f"/{slug}", headers={"Accept": "application/json"})
    assert check10.status_code in [404, 410]
