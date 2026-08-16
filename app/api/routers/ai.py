from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Query

from app.api.dependencies import TOKEN_DEP, SettingsDep, PROJECT_SERVICE_DEP, \
    OPEN_AI_DEP, GEMINI_DEP
from app.client.ai_client import AiClient
from app.core.security import decode_token
from app.schemas.ai import Suggestions, Preferences

router = APIRouter(prefix="/projects", tags=["AI"])


@router.post("/{project_id}/ai_suggestions", status_code=status.HTTP_200_OK, response_model=Suggestions)
async def get_ai_suggestions(
        token: TOKEN_DEP,
        project_service: PROJECT_SERVICE_DEP,
        settings: SettingsDep,
        project_id: int,
        client_gemini: GEMINI_DEP,
        client_openai: OPEN_AI_DEP,
        data: Preferences,
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
    }
    if model and model.lower() == "gpt":
        client = AiClient(client_openai, settings)
        return await client.get_suggestions_openai(**payload)

    client = AiClient(client_gemini, settings)
    return await client.get_suggestions_gemini(**payload)
