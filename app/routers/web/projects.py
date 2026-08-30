from typing import Any, Annotated

import pydantic
from fastapi import APIRouter, status, HTTPException
from fastapi.params import Query, Form
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.core.exc_handler import WebAuthRequired
from app.core.templates import templates
from app.routers.dependencies import PROJECT_SERVICE_DEP, CLIENT, \
    WEB_USER_ID_DEP, SettingsDep, PLACE_SERVICE_DEP
from app.schemas.project import ProjectUpdate
from app.schemas.web.project import ProjectCreateForm

router = APIRouter(prefix="/web/projects", tags=["web"])

PROJECT_CREATE_FORM = Annotated[ProjectCreateForm, Form()]

@router.post(
    "/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
        request: Request,
        project_service: PROJECT_SERVICE_DEP,
        user_id: WEB_USER_ID_DEP,
        client: CLIENT,
        settings: SettingsDep,
        project_schema: PROJECT_CREATE_FORM,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    try:
        await project_service.create(user_id, project_schema, client,settings)
        return RedirectResponse(
            url="/web/projects/",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/create_project.html",
            context={"error": exc.detail},
            status_code=exc.status_code,
        )


@router.get("/",response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_projects(
        request: Request,
        project_service: PROJECT_SERVICE_DEP,
        user_id: WEB_USER_ID_DEP,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(le=10)] = 10,
        is_completed: Annotated[bool | None, Query()] = None,
        search: Annotated[str | None, Query()] = None,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    params = {
        "user_id": user_id,
        "offset": offset,
        "limit": limit,
        "is_completed": is_completed,
        "search": search,
    }
    projects = await project_service.get_all_paginated(**params)

    return templates.TemplateResponse(
        request=request,
        name="main/get_projects.html",
        context={"projects": projects},
    )


@router.get(
    "/{project_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def get_project(
        request: Request,
        project_service: PROJECT_SERVICE_DEP,
        place_service: PLACE_SERVICE_DEP,
        user_id: WEB_USER_ID_DEP,
        project_id: int,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(le=10)] = 10,
        is_visited: Annotated[bool | None, Query()] = None,
        search: Annotated[str | None, Query()] = None,
) -> Any:
    if user_id is None:
        raise WEB_USER_ID_DEP
    try:
        params = {
            "user_id": user_id,
            "project_id": project_id,
            "offset": offset,
            "limit": limit,
            "is_visited": is_visited,
            "search": search,
        }
        project = await project_service.get_one(user_id, project_id)
        places = await place_service.get_all_paginated(**params)
        return templates.TemplateResponse(
            request=request,
            name="main/get_project.html",
            context={
                "project": project,
                "places": places,
            },
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/get_projects.html",
            context={"error": exc.detail},
            status_code=exc.status_code,
        )


@router.post("/{project_id}/delete")
async def delete_project(
        request: Request,
        project_service: PROJECT_SERVICE_DEP,
        user_id: WEB_USER_ID_DEP,
        project_id: int,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(le=10)] = 10,
        is_completed: Annotated[bool | None, Query()] = None,
        search: Annotated[str | None, Query()] = None,
) -> Any:
    if user_id is None:
        raise WebAuthRequired

    try:
        await project_service.get_with_visited_places(user_id, project_id)
        await project_service.delete(user_id, project_id)
        return RedirectResponse(
            url="/web/projects/",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except HTTPException as exc:
        params = {
            "user_id": user_id,
            "offset": offset,
            "limit": limit,
            "is_completed": is_completed,
            "search": search,
        }
        projects = await project_service.get_all_paginated(**params)
        return templates.TemplateResponse(
            request=request,
            name="main/get_projects.html",
            context={
                "projects": projects,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )


@router.post(
    "/{project_id}/update",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def update_project(
        request: Request,
        project_service: PROJECT_SERVICE_DEP,
        user_id: WEB_USER_ID_DEP,
        project_id: int,
        name: str | None = Form(default=None),
        description: str | None = Form(default=None),
        start_date: str | None = Form(default=None),
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    project = await project_service.get_one(user_id, project_id)
    try:
        data_updated = {
            "name": name,
            "description": description,
            "start_date": start_date,
        }
        project_update = ProjectUpdate.model_validate(data_updated).model_dump(exclude_none=True)
        await project_service.update(user_id, project_id, project_update)
        return RedirectResponse(
            url="/web/projects/",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/update_project.html",
            status_code=exc.status_code,
            context={
                "project": project,
                "error": exc.detail,
            }
        )
    except pydantic.ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/update_project.html",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            context={
                "project": project,
                "errors": exc.errors(),
            }
        )
