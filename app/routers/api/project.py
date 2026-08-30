from typing import Any, Annotated

from fastapi import APIRouter, Body
from fastapi.params import Query
from starlette.requests import Request

from app.routers.dependencies import PROJECT_SERVICE_DEP, TOKEN_DEP, REDIS_CLIENT, \
    CLIENT, SettingsDep
from app.core.security import decode_token
from app.schemas.project import ProjectRead, ProjectCreate, ProjectUpdate
from cache.keys import projects_key, project_key, project_pattern, \
    projects_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/projects", tags=["projects"])
PROJECT_CREATE = Annotated[ProjectCreate, Body()]
PROJECT_UPDATE = Annotated[ProjectUpdate, Body()]


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project_service: PROJECT_SERVICE_DEP,
    token: TOKEN_DEP,
    settings: SettingsDep,
    redis_client: REDIS_CLIENT,
    project_schema: PROJECT_CREATE,
    request: Request,
    client: CLIENT,
):
    user_id = decode_token(token, settings)
    cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)
    await cache.rate_limit_by_ip(request, settings)

    project_read = await project_service.create(user_id, project_schema, client, settings)

    await cache.delete_by_pattern(projects_pattern(user_id))
    await cache.delete_by_pattern(project_pattern(user_id))
    return project_read


@router.get("/", response_model=list[ProjectRead])
async def get_projects(
    project_service: PROJECT_SERVICE_DEP,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    settings: SettingsDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(le=5)] = 5,
    is_completed: Annotated[bool | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> Any:
    user_id = decode_token(token, settings)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    params = {
        "user_id": user_id,
        "offset": offset,
        "limit": limit,
        "is_completed": is_completed,
        "search": search,
    }
    cached_projects = await cache.get(projects_key(**params))

    if cached_projects is not None:
        return cached_projects

    projects_read = await project_service.get_all_paginated(**params)

    projects_for_cache = [project.model_dump(mode="json") for project in projects_read]
    await cache.set_cache(projects_key(**params), projects_for_cache)

    return projects_read


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_service: PROJECT_SERVICE_DEP,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    settings: SettingsDep,
    project_id: int,
) -> ProjectRead:
    user_id = decode_token(token, settings)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_project = await cache.get(project_key(user_id, project_id))

    if cached_project is not None:
        return cached_project

    project_read = await project_service.get_one(user_id, project_id)

    project_for_cache = project_read.model_dump(mode="json")
    await cache.set_cache(project_key(user_id, project_id), project_for_cache)

    return project_read


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_service: PROJECT_SERVICE_DEP,
    token: TOKEN_DEP,
    project_id: int,
    project_update: PROJECT_UPDATE,
    redis: REDIS_CLIENT,
    settings: SettingsDep,
) -> ProjectRead:
    user_id = decode_token(token, settings)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)

    updated_data = project_update.model_dump(exclude_unset=True)
    project = await project_service.update(user_id, project_id, updated_data)

    await cache.invalidate_projects(user_id, project_id)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_service: PROJECT_SERVICE_DEP,
    token: TOKEN_DEP,
    redis: REDIS_CLIENT,
    settings: SettingsDep,
    project_id: int,
) -> Any:
    user_id = decode_token(token, settings)
    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    project = await project_service.get_one(user_id, project_id)
    await project_service.get_with_visited_places(user_id, project_id)

    await project_service.delete(user_id, project_id)

    await cache.invalidate_projects(user_id, project_id)
    return {"detail": f"Project {project.name} deleted successfully!"}
