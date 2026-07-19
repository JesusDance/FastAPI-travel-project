from typing import Any, Annotated

from fastapi import APIRouter, Body
from starlette.requests import Request

from app.client.client import ArticAPIClient
from app.config.config import settings
from app.dependencies import (
    TOKEN_DEP,
    CLIENT,
    REDIS_CLIENT,
    PLACE_SERVICE_DEP,
    PROJECT_SERVICE_DEP,
)
from app.schemas.place import PlaceUpdate, PlaceRead, PlaceCreate
from app.security import decode_token
from cache.keys import places_key, place_key, place_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/projects", tags=["place"])
PLACE_CREATE = Annotated[PlaceCreate, Body()]
PLACE_UPDATE = Annotated[PlaceUpdate, Body()]
PLACE_READ = Annotated[PlaceRead, Body()]


@router.post("/{project_id}/places", response_model=PlaceRead, status_code=201)
async def add_place(
    project_id: int,
    client: CLIENT,
    place_schema: PLACE_CREATE,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    request: Request,
    place_service: PLACE_SERVICE_DEP,
    project_service: PROJECT_SERVICE_DEP,
) -> Any:
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    await cache.rate_limit_by_ip(request)
    await project_service.get_one(user_id, project_id)
    await place_service.get_all(user_id, project_id)
    await place_service.get_one_by_external_id(
        user_id, project_id, place_schema.external_id
    )

    api_client = ArticAPIClient(settings.ARTIC_API_URL, client)
    title = await api_client.fetch_place_from_api(place_schema.external_id)

    place = await place_service.create(user_id, project_id, place_schema, title)

    await cache.delete_by_pattern(place_pattern(user_id, project_id))
    await cache.delete(places_key(user_id, project_id))
    await cache.invalidate_projects(user_id, project_id)

    return place


@router.get("/{project_id}/places", response_model=list[PlaceRead])
async def get_places(
    project_id: int,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    place_service: PLACE_SERVICE_DEP,
    project_service: PROJECT_SERVICE_DEP,
) -> list[PlaceRead]:
    user_id = decode_token(token)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_places = await cache.get(places_key(user_id, project_id))

    if cached_places is not None:
        return cached_places

    await project_service.get_one(user_id, project_id)

    places_read = await place_service.get_all(user_id, project_id)

    places_for_cache = [place.model_dump() for place in places_read]
    await cache.set_cache(places_key(user_id, project_id), places_for_cache)

    return places_read


@router.get("/{project_id}/places/{place_id}", response_model=PlaceRead)
async def get_place(
    project_id: int,
    place_id: int,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    place_service: PLACE_SERVICE_DEP,
) -> PlaceRead:
    user_id = decode_token(token)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_place = await cache.get(place_key(user_id, project_id, place_id))

    if cached_place is not None:
        return cached_place

    place_read = await place_service.get_one(user_id, project_id, place_id)

    place_for_cache = place_read.model_dump()
    await cache.set_cache(place_key(user_id, project_id, place_id), place_for_cache)

    return place_read


@router.patch("/{project_id}/places/{place_id}", response_model=PlaceRead)
async def update_place(
    project_id: int,
    place_id: int,
    place: PLACE_UPDATE,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    place_service: PLACE_SERVICE_DEP,
) -> PlaceRead:
    user_id = decode_token(token)
    updated_data = place.model_dump(exclude_unset=True)

    place_db = await place_service.update(user_id, project_id, place_id, updated_data)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    await cache.invalidate_projects(user_id, project_id)
    await cache.invalidate_places(user_id, project_id, place_id)

    return place_db
