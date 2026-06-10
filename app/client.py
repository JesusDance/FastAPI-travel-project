import httpx
from httpx import AsyncClient
from fastapi import HTTPException


class ArticAPIClient:
    def __init__(self, url):
        self.url = url

    async def fetch_place_from_api(self, external_id: int) -> str:
        url = f"{self.url}/{external_id}"
        try:
            async with AsyncClient(http2=True) as client:
                response = await client.get(url, timeout=10)
                response.raise_for_status()
                data = response.json().get("data")
                if not data:
                    raise HTTPException(404, "Invalid response from API")
                return data.get("title", "Unknown")

        except httpx.TimeoutException:
            raise HTTPException(504, "External API timeout")

        except httpx.RequestError:
            raise HTTPException(404, "Place not found in external API")
