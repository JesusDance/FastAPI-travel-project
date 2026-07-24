import httpx
from fastapi import HTTPException
from starlette.requests import Request

from app.core.logger import logger


def get_httpx_client(r: Request) -> httpx.AsyncClient:
    return r.app.state.httpx_client


class ArticAPIClient:
    def __init__(self, url, client: httpx.AsyncClient):
        self.url = url
        self.client = client

    async def fetch_place_from_api(self, external_id: int) -> str:
        logger.info("Fetching data from external API", extra={"external_ip": external_id})
        url = f"{self.url}/{external_id}"
        try:
            response = await self.client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get("data")
            if not data:
                logger.warning("Invalid response from API", extra={"external_ip": external_id})
                raise HTTPException(404, "Invalid response from API")
            return data.get("title", "Unknown")

        except httpx.TimeoutException:
            logger.warning("External API timeout",
                           extra={"external_ip": external_id})
            raise HTTPException(504, "External API timeout")

        except httpx.HTTPStatusError:
            logger.warning("Place not found in external API",
                           extra={"external_ip": external_id})
            raise HTTPException(404, "Place not found in external API")

        except httpx.RequestError:
            logger.warning("Place not found in external API",
                           extra={"external_ip": external_id})
            raise HTTPException(404, "Place not found in external API")
