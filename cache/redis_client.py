import json
from typing import Any

from fastapi import HTTPException
from fastapi import status
from redis.asyncio import Redis
from starlette.requests import Request

from app.config import settings
from cache.keys import project_key, projects_key, places_key, place_key
from app.logger import logger

def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client


class RedisCacheClient:
    def __init__(self, client: Redis, cache_ttl_seconds: int | None = None):
        self.client = client
        self.cache_ttl_seconds = cache_ttl_seconds


    async def set_cache(self, key: str, value: dict | list) -> Any:
        try:
            result = await self.client.set(
                name=key, value=json.dumps(value), ex=self.cache_ttl_seconds
            )
            return result
        except Exception:
            logger.exception("Cannot set cache", extra={"key": key})


    async def get(self, key: str) -> Any:
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            logger.exception("Cannot get cache", extra={"key": key})
            return None


    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception:
            logger.exception("Failed to invalidate", extra={"key": key})


    async def delete_by_pattern(self, pattern: str) -> None:
        try:
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
        except Exception:
            logger.exception(
                "Failed to invalidate by pattern", extra={"pattern": pattern}
            )


    async def rate_limit_by_ip(
            self, r: Request,
            seconds: int = settings.CACHE_EXPIRE_SECONDS,
            limit: int = settings.LIMIT_OF_REQUESTS,
    ):
        credentials = HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests"
        )

        ip = r.client.host
        key = f"rate_limit: {ip}"
        request = await self.client.incr(key)

        if request == 1:
            await self.client.expire(name=key, time=seconds)

        if request > limit:
            raise credentials


    async def invalidate_projects(self, user_id: int, project_id: int) -> None:
        try:
            await self.client.delete(projects_key(user_id))
            await self.client.delete(project_key(user_id, project_id))
        except Exception:
            logger.exception("Failed to invalidate projects cache")


    async def invalidate_places(self, user_id: int, project_id: int, place_id: int) -> None:
        try:
            await self.client.delete(places_key(user_id, project_id))
            await self.client.delete(place_key(user_id, project_id, place_id))
        except Exception:
            logger.exception("Failed to invalidate places cache")
