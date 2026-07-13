from typing import Any

from fastapi import HTTPException, APIRouter
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from app.client import ArticAPIClient
from app.config import settings
from app.db import SessionDep
from app.dependencies import CLIENT, TOKEN_DEP, REDIS_CLIENT, \
    UPDATE_PROJECT
from app.models import Project, Place
from app.schemas import ProjectCreate, ProjectRead
from app.security import decode_token
from cache.keys import projects_key, project_key, project_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    session: SessionDep,
    client: CLIENT,
    data: ProjectCreate,
    token: TOKEN_DEP,
    redis_client: REDIS_CLIENT,
    request: Request,
) -> Any:
    user_id = decode_token(token)

    cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)

    await cache.rate_limit_by_ip(request)

    existing_project = await session.scalar(
        select(Project)
        .where(Project.name == data.name, Project.user_id == user_id)
    )

    if existing_project:
        raise HTTPException(409, "Project already exists")

    project = Project(**data.model_dump(exclude={"places"}), user_id=user_id)
    session.add(project)
    await session.flush()

    api_client = ArticAPIClient(settings.ARTIC_API_URL, client)

    external_ids = [place.external_id for place in data.places]

    if len(external_ids) > 10:
        raise HTTPException(400, "Max 10 places per project")

    if len(external_ids) != len(set(external_ids)):
        raise HTTPException(409, "Place already exists in project")

    for place in data.places:
        title = await api_client.fetch_place_from_api(place.external_id)

        db_place = Place(
            project_id=project.id,
            external_id=place.external_id,
            title=title,
            user_id=user_id,
        )

        session.add(db_place)

    await session.commit()

    await cache.delete(projects_key(user_id))
    await cache.delete_by_pattern(project_pattern(user_id))

    await session.refresh(project)
    return project


@router.get("/", response_model=list[ProjectRead])
async def get_projects(session: SessionDep, token: TOKEN_DEP, redis: REDIS_CLIENT):
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_projects = await cache.get(projects_key(user_id))

    if cached_projects is not None:
        return cached_projects

    projects = (await session.scalars(
        select(Project)
        .where(Project.user_id == user_id))
                ).all()

    projects_read = [ProjectRead.model_validate(project) for project in projects]
    projects_for_cache = [project.model_dump(mode="json") for project in projects_read]
    await cache.set_cache(projects_key(user_id), projects_for_cache)

    return projects_read


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
        session: SessionDep,
        project_id: int,
        token: TOKEN_DEP,
        redis: REDIS_CLIENT
):
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)
    cached_project = await cache.get(project_key(user_id, project_id))

    if cached_project is not None:
        return cached_project

    project = await session.scalar(
        select(Project)
        .where(Project.user_id == user_id, Project.id == project_id)
    )

    if not project:
        raise HTTPException(404, "Project not found")

    project_for_cache = ProjectRead.model_validate(project).model_dump(mode="json")
    await cache.set_cache(project_key(user_id, project_id), project_for_cache)

    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    session: SessionDep,
        project_id: int,
        data: UPDATE_PROJECT,
        token: TOKEN_DEP,
        redis: REDIS_CLIENT,
):
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)

    updated_data = data.model_dump(exclude_unset=True)

    if not updated_data:
        raise HTTPException(422, "No fields to update")

    project = await session.scalar(
        update(Project)
        .where(Project.user_id == user_id, Project.id == project_id)
        .values(**updated_data)
        .returning(Project)
    )

    if not project:
        raise HTTPException(404, "Project not found")

    #update_project_completion(session, project)

    # session.add() - робота з об'єктом ОРМ тут не потрібен, update це вираз
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(422, detail=f"{e.orig}")
    #session.refresh(project) проект вже повернен через update.returning()

    await cache.invalidate_projects(user_id, project_id)

    return project


@router.delete("/{project_id}")
async def delete_project(
        session: SessionDep,
        project_id: int,
        token: TOKEN_DEP,
        redis: REDIS_CLIENT
):
    user_id = decode_token(token)

    cache = RedisCacheClient(redis, settings.CACHE_TTL_SECONDS)

    project = await session.scalar(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    )

    if not project:
        raise HTTPException(404, "Project not found")

    visited_exists = await session.scalar(
        select(Place).where(Place.project_id == project_id, Place.is_visited == True)
    )

    if visited_exists:
        raise HTTPException(400, "Cannot delete project with visited places")

    await session.delete(project)
    await session.commit()
    await cache.invalidate_projects(user_id, project_id)

    return {"detail": "Project deleted"}
