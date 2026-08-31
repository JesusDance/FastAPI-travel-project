from typing import Any, Annotated

from fastapi import APIRouter, status, Query, HTTPException
from fastapi.params import Form
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.client.ai_client import AiClient
from app.core.templates import templates
from app.routers.dependencies import WEB_USER_ID_DEP, WebAuthRequired, \
    PROJECT_SERVICE_DEP, OPEN_AI_DEP, GEMINI_DEP, SettingsDep
from app.schemas.ai import Preferences

router = APIRouter(prefix="/web/projects", tags=["ai"])

PREFERENCES = Annotated[Preferences, Form()]


@router.post(
    "/{project_id}/ai_suggestions",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK
)
async def get_ai_suggestions(
        request: Request,
        user_id: WEB_USER_ID_DEP,
        project_service: PROJECT_SERVICE_DEP,
        client_gemini: GEMINI_DEP,
        client_openai: OPEN_AI_DEP,
        settings: SettingsDep,
        project_id: int,
        data: PREFERENCES,
        model: Annotated[str | None, Query(max_length=3)] = None,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    try:
        project = await project_service.get_one(user_id, project_id)
        places_title = [place.title for place in project.places if place.title]
        payload = {
            "existing_places": places_title,
            "project_name": project.name,
            "project_description": project.description,
            "days": data.days,
            "preferences": data.preferences,
        }

        if model and model.lower() == "gpt":
            client = AiClient(client_openai, settings)
            suggestions = await client.get_suggestions_openai(**payload)
            return templates.TemplateResponse(
                request=request,
                name="main/get_suggestions.html",
                context={"suggestions": suggestions},
            )
        client = AiClient(client_gemini, settings)
        suggestions = await client.get_suggestions_gemini(**payload)
        return templates.TemplateResponse(
            request=request,
            name="main/get_suggestions.html",
            context={"suggestions": suggestions},
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/ai_suggestions.html",
            context={
                "project_id": project_id,
                "error": exc.detail
            },
            status_code=exc.status_code,
        )
