import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_link(client: AsyncClient):
    payload = {
        "destination_url": "https://github.com/dixtuel",
        "slug": "dixtuel-gh",
        "title": "Asrin Github Profile",
    }
    response = await client.post("/api/v1/links", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "dixtuel-gh"
    assert data["destination_url"] == "https://github.com/dixtuel"

    # List links
    list_res = await client.get("/api/v1/links")
    assert list_res.status_code == 200
    links = list_res.json()
    assert len(links) >= 1
