from typing import Any, Annotated

from fastapi import APIRouter, status, Query, HTTPException
from fastapi.params import Form
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from app.client.ai_client import AiClient
from app.core.templates import templates
from app.routers.dependencies import WEB_USER_ID_DEP, WebAuthRequired, \
    PROJECT_SERVICE_DEP, OPEN_AI_DEP, GEMINI_DEP, SettingsDep, \
    PLACE_SERVICE_DEP, REDIS_CLIENT
from app.schemas.ai import Preferences
from cache.keys import ai_suggestions, ai_suggestion, places_pattern, \
    place_pattern, ai_suggestion_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/web/projects", tags=["ai"])

PREFERENCES = Annotated[Preferences, Form()]


@router.post(
    "/{project_id}/ai_suggestions",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
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
        redis_client: REDIS_CLIENT,
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
            "settings": settings,
        }

        if model and model.lower() == "gpt":
            client = AiClient(client_openai, settings)
            suggestions = await client.get_suggestions_openai(**payload)

            cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)
            suggestions_for_cache = suggestions.model_dump()
            await cache.set_cache(ai_suggestions(user_id, project_id),
                                  suggestions_for_cache)

            for suggestion in suggestions_for_cache["suggestions"]:
                await cache.set_cache(
                    ai_suggestion(user_id, project_id, suggestion["external_id"]),
                                  suggestion)

            return templates.TemplateResponse(
                request=request,
                name="main/get_suggestions.html",
                context={"suggestions": suggestions, "project_id": project_id},
            )
        else:
            client = AiClient(client_gemini, settings)
            suggestions = await client.get_suggestions_gemini(**payload)

            cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)
            suggestions_for_cache = suggestions.model_dump()
            await cache.set_cache(ai_suggestions(user_id, project_id),
                                  suggestions_for_cache)

            for suggestion in suggestions_for_cache["suggestions"]:
                await cache.set_cache(
                    ai_suggestion(user_id, project_id, suggestion["external_id"]),
                                  suggestion)

            return templates.TemplateResponse(
                request=request,
                name="main/get_suggestions.html",
                context={"suggestions": suggestions, "project_id": project_id},
            )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/ai_suggestions.html",
            context={
                "project_id": project_id,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )


@router.post(
    "/{project_id}/ai_suggestions/add/{external_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ai_suggestion_add(
        request: Request,
        project_id: int,
        external_id: int,
        place_service: PLACE_SERVICE_DEP,
        settings: SettingsDep,
        user_id: WEB_USER_ID_DEP,
        redis_client: REDIS_CLIENT,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    try:
        cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)
        suggestion = await cache.get(ai_suggestion(user_id, project_id, external_id))

        payload = {
                "user_id": user_id,
                "project_id": project_id,
                "external_id": external_id,
                "settings": settings,
                "title": suggestion["title"],
            }
        await place_service.create(**payload)
        await cache.invalidate_projects(user_id, project_id)
        await cache.delete_by_pattern(ai_suggestions(user_id, project_id))
        await cache.delete_by_pattern(places_pattern(user_id, project_id))
        await cache.delete_by_pattern(place_pattern(user_id, project_id))
        await cache.delete_by_pattern(ai_suggestion_pattern(user_id, project_id))
        return RedirectResponse(
            f"/web/projects/{project_id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="main/ai_suggestions.html",
            context={
                "project_id": project_id,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )