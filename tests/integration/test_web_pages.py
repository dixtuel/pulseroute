import asyncio

import pytest
from httpx import AsyncClient

from pulseroute.main import app


@pytest.mark.asyncio
async def test_render_root_and_dashboard(client: AsyncClient):
    res_root = await client.get("/", headers={"Accept": "text/html"})
    assert res_root.status_code == 200
    assert "PulseRoute" in res_root.text

    res_dash = await client.get("/dashboard", headers={"Accept": "text/html"})
    assert res_dash.status_code == 200
    assert "PulseRoute" in res_dash.text


@pytest.mark.asyncio
async def test_keepalive_never_checks_external_services(client: AsyncClient, monkeypatch):
    async def unexpected_call(*args, **kwargs):
        raise AssertionError("keepalive must not access external services")

    monkeypatch.setattr("pulseroute.main.get_redis", unexpected_call)
    monkeypatch.setattr("pulseroute.main.async_session_maker", unexpected_call)
    res = await client.get("/healtalive")
    assert res.status_code == 200
    assert res.text == "alive\n"
    assert res.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_app_starts_when_database_is_unavailable(client: AsyncClient, monkeypatch):
    async def db_unavailable():
        raise ConnectionError("database is unavailable")

    async def idle_worker():
        await asyncio.Event().wait()

    async def close_redis():
        pass

    monkeypatch.setattr("pulseroute.main.init_db", db_unavailable)
    monkeypatch.setattr("pulseroute.main.run_analytics_batch_worker", idle_worker)
    monkeypatch.setattr("pulseroute.main.run_dns_verification_worker", idle_worker)
    monkeypatch.setattr("pulseroute.main.close_redis", close_redis)

    async with app.router.lifespan_context(app):
        response = await client.get("/healtalive")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_render_privacy_and_terms(client: AsyncClient):
    res_priv = await client.get("/privacy", headers={"Accept": "text/html"})
    assert res_priv.status_code == 200
    assert "Privacy Policy" in res_priv.text

    res_terms = await client.get("/terms", headers={"Accept": "text/html"})
    assert res_terms.status_code == 200
    assert "Terms of Service" in res_terms.text


@pytest.mark.asyncio
async def test_render_custom_404_html(client: AsyncClient):
    res_404 = await client.get("/not-found-xyz-abc", headers={"Accept": "text/html"})
    assert res_404.status_code == 404
    assert "Short Link Not Found" in res_404.text


@pytest.mark.asyncio
async def test_static_cache_control_and_gzip(client: AsyncClient):
    # Test static asset caching headers
    res_static = await client.get("/static/favicon.svg")
    if res_static.status_code == 200:
        assert "max-age=604800" in res_static.headers.get("cache-control", "")

    # Test robots.txt API disallow
    res_robots = await client.get("/robots.txt")
    assert res_robots.status_code == 200
    assert "Disallow: /api/" in res_robots.text
    assert "Disallow: /internal/" in res_robots.text

    # Test gzip compression
    res_gzip = await client.get("/", headers={"Accept-Encoding": "gzip", "Accept": "text/html"})
    assert res_gzip.status_code == 200
    assert res_gzip.headers.get("content-encoding") == "gzip"
