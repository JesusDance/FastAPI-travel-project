from typing import Any

from fastapi import HTTPException, APIRouter
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from app.client import ArticAPIClient
from app.config import settings
from app.db import SessionDep
from app.dependencies import (
    TOKEN_DEP,
    CLIENT,
    REDIS_CLIENT,
)
from app.models import Place, Project
from app.schemas import PlaceUpdate, PlaceRead, PlaceCreate
from app.security import decode_token
from app.validation import check_places_limit, update_project_completion
from cache.keys import places_key, place_key, place_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/projects", tags=["place"])


@router.post("/{project_id}/places", response_model=PlaceRead, status_code=201)
async def add_place(
    session: SessionDep,
    project_id: int,
    client: CLIENT,
    place: PlaceCreate,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    request: Request,
) -> Any:
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    await cache.rate_limit_by_ip(request)

    project = await session.scalar(
        select(Project)
        .where(Project.user_id == user_id, Project.id == project_id)
    )

    if not project:
        raise HTTPException(404, "Project not found")

    await check_places_limit(session, project_id)

    existing_place = await session.scalar(
        select(Place)
        .where(
            Place.user_id == user_id,
            Place.project_id == project_id,
            Place.external_id == place.external_id,
        )
    )

    if existing_place:
        raise HTTPException(409, "Place already exists in project")

    api_client = ArticAPIClient(settings.ARTIC_API_URL, client)
    title = await api_client.fetch_place_from_api(place.external_id)

    place = Place(
        project_id=project_id,
        external_id=place.external_id,
        title=title,
        user_id=user_id,
    )

    session.add(place)
    await session.commit()

    await cache.delete_by_pattern(place_pattern(user_id, project_id))
    await cache.delete(places_key(user_id, project_id))
    await cache.invalidate_projects(user_id, project_id)

    await session.refresh(place)

    return place


@router.get("/{project_id}/places", response_model=list[PlaceRead])
async def get_places(
        session: SessionDep,
        project_id: int,
        token: TOKEN_DEP,
        redis: REDIS_CLIENT
) -> Any:
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_places = await cache.get(places_key(user_id, project_id))

    if cached_places is not None:
        return cached_places

    project = await session.scalar(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    )
    if not project:
        raise HTTPException(404, "Project not found")

    places = (await session.scalars(
        select(Place)
        .where(Place.project_id == project_id))).all()

    places_read = [PlaceRead.model_validate(place) for place in places]
    places_for_cache = [place.model_dump() for place in places_read]
    await cache.set_cache(places_key(user_id, project_id), places_for_cache)

    return places_read


@router.get("/{project_id}/places/{place_id}", response_model=PlaceRead)
async def get_place(
    session: SessionDep,
    project_id: int,
    place_id: int,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
) -> Any:
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_place = await cache.get(place_key(user_id, project_id, place_id))

    if cached_place is not None:
        return cached_place

    place = await session.scalar(
        select(Place)
        .join(Project, Place.project_id == Project.id)
        .where(
            Project.user_id == user_id, Project.id == project_id, Place.id == place_id
        )
    )

    if not place:
        raise HTTPException(404, "Place not found")

    place_for_cache = PlaceRead.model_validate(place).model_dump()
    await cache.set_cache(place_key(user_id, project_id, place_id), place_for_cache)

    return place


@router.patch("/{project_id}/places/{place_id}", response_model=PlaceRead)
async def update_place(
    session: SessionDep,
    project_id: int,
    place_id: int,
    place: PlaceUpdate,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
) -> Any:

    user_id = decode_token(token)

    updated_data = place.model_dump(exclude_unset=True)

    if not updated_data:
        raise HTTPException(404, "No fields to update")

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)

    place_db = await session.scalar(
        update(Place)
        .where(Place.user_id == user_id,
               Place.project_id == project_id,
               Place.id == place_id)
        .values(**updated_data)
        .returning(Place)
    )

    if not place_db:
        raise HTTPException(404, "Place not found")
    #session.add(place_db) - робота з об'єктом ОРМ тут не потрібен, update це вираз

    project = await session.scalar(
        select(Project)
        .where(Project.user_id == user_id, Project.id == project_id)
    )

    if not project:
        raise HTTPException(404, "Project not found")

    await update_project_completion(session, project)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(422, detail=f"{e.orig}")
    #session.refresh(place_db) проект вже повернен через update.returning()

    await cache.invalidate_projects(user_id, project_id)
    await cache.invalidate_places(user_id, project_id, place_id)

    return place_db
