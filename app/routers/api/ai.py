from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Query, Body

from app.client.ai_client import AiClient
from app.core.security import decode_token
from app.routers.dependencies import TOKEN_DEP, SettingsDep, \
    PROJECT_SERVICE_DEP, \
    OPEN_AI_DEP, GEMINI_DEP, REDIS_CLIENT, PLACE_SERVICE_DEP
from app.schemas.ai import Suggestions, Preferences, PlaceAiCreate
from app.schemas.place import PlaceRead
from cache.keys import ai_suggestions, places_pattern, place_pattern, \
    ai_suggestion_pattern
from cache.redis_client import RedisCacheClient

router = APIRouter(prefix="/projects", tags=["AI"])

PLACE_AI_CREATE = Annotated[PlaceAiCreate, Body()]


@router.post(
    "/{project_id}/ai_suggestions",
    status_code=status.HTTP_200_OK,
    response_model=Suggestions,
)
async def get_ai_suggestions(
        token: TOKEN_DEP,
        project_service: PROJECT_SERVICE_DEP,
        settings: SettingsDep,
        project_id: int,
        client_gemini: GEMINI_DEP,
        client_openai: OPEN_AI_DEP,
        data: Preferences,
        redis_client: REDIS_CLIENT,
        model: Annotated[str | None, Query(max_length=3)] = None,
) -> Suggestions:
    user_id = decode_token(token, settings)
    project = await project_service.get_one(user_id, project_id)
    existing_places = [place.title for place in project.places if place.title]

    payload = {
        "existing_places": existing_places,
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

        return suggestions

    else:
        client = AiClient(client_gemini, settings)
        suggestions = await client.get_suggestions_gemini(**payload)
        suggestions_for_cache = suggestions.model_dump()
        cache = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)
        await cache.set_cache(ai_suggestions(user_id, project_id), suggestions_for_cache)

        return suggestions


@router.post(
    "/{project_id}/ai_suggestions/add",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaceRead,
)
async def add_suggestion_to_db(
        project_id: int,
        redis_client: REDIS_CLIENT,
        settings: SettingsDep,
        token: TOKEN_DEP,
        place_service: PLACE_SERVICE_DEP,
        place_ai_schema: PlaceAiCreate,
) -> PlaceRead:
    user_id = decode_token(token, settings)
    client = RedisCacheClient(redis_client, settings.CACHE_TTL_SECONDS)

    #response = await client.get(ai_suggestions(user_id, project_id))

    params = {
        "user_id": user_id,
        "project_id": project_id,
        "ai_schema": place_ai_schema,
        "settings": settings,
    }

    place = await place_service.create(**params)

    await client.invalidate_projects(user_id, project_id)
    await client.delete_by_pattern(places_pattern(user_id, project_id))
    await client.delete_by_pattern(place_pattern(user_id, project_id))
    await client.delete_by_pattern(ai_suggestions(user_id, project_id))
    await client.delete_by_pattern(ai_suggestion_pattern(user_id, project_id))
    return place