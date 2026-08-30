from typing import Any, Annotated

from fastapi import APIRouter, status, HTTPException, Form
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from app.core.exc_handler import WebAuthRequired
from app.core.templates import templates
from app.routers.dependencies import WEB_USER_ID_DEP, PLACE_SERVICE_DEP, \
    CLIENT, SettingsDep
from app.schemas.place import PlaceCreate
from app.schemas.web.place import PlaceUpdateForm

router = APIRouter(prefix="/web/projects", tags=["place"])

PLACE_CREATE = Annotated[PlaceCreate, Form()]
PLACE_UPDATE = Annotated[PlaceUpdateForm, Form()]


@router.post(
    "/{project_id}/places/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_place(
        request: Request,
        user_id: WEB_USER_ID_DEP,
        place_service: PLACE_SERVICE_DEP,
        project_id: int,
        place_schema: PLACE_CREATE,
        client: CLIENT,
        settings: SettingsDep,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    try:
        await place_service.create(user_id, project_id, place_schema, client, settings)
        return RedirectResponse(f"/web/projects/{project_id}", status.HTTP_303_SEE_OTHER)
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/create_place.html",
            context={
                "project_id": project_id,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )


@router.post(
    "/{project_id}/places/{place_id}/update",
    response_class=HTMLResponse,
)
async def update_place(
        request: Request,
        user_id: WEB_USER_ID_DEP,
        place_service: PLACE_SERVICE_DEP,
        project_id: int,
        place_id: int,
        place_schema: PLACE_UPDATE,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    try:
        updated_place = place_schema.model_dump(exclude_none=True)
        await place_service.update(user_id, project_id, place_id, updated_place)
        return RedirectResponse(
            url=f"/web/projects/{project_id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/update_place.html",
            context={
                "place_id": place_id,
                "project_id": project_id,
                "error": exc.detail
            },
            status_code=exc.status_code,
        )

