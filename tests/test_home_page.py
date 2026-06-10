import pytest


@pytest.mark.asyncio
async def test_home_page(test_client_api):
    response = await test_client_api.get("/")
    json_response = response.json()

    assert response.status_code == 200
    assert "message" in json_response
    assert json_response["message"] == "Hello from backend!"
