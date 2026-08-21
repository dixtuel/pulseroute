import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_render_root_and_dashboard(client: AsyncClient):
    res_root = await client.get("/", headers={"Accept": "text/html"})
    assert res_root.status_code == 200
    assert "PulseRoute" in res_root.text

    res_dash = await client.get("/dashboard", headers={"Accept": "text/html"})
    assert res_dash.status_code == 200
    assert "PulseRoute" in res_dash.text


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
