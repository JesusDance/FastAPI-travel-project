from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient
from redis.asyncio import Redis

from app.client.client import get_httpx_client
from app.config.config import  Settings, get_settings_from_lifespan
from app.db.session import SessionDep
from app.services.place import PlaceService
from app.services.project import ProjectService
from cache.redis_client import get_redis_client


def get_project_service(session: SessionDep) -> ProjectService:
    return ProjectService(session)


def get_place_service(session: SessionDep) ->PlaceService:
    return PlaceService(session)


oauth2_schema = OAuth2PasswordBearer(tokenUrl="/register/login")

TOKEN_DEP = Annotated[str, Depends(oauth2_schema)]
CLIENT = Annotated[AsyncClient, Depends(get_httpx_client)]
REDIS_CLIENT = Annotated[Redis, Depends(get_redis_client)]
PROJECT_SERVICE_DEP = Annotated[ProjectService, Depends(get_project_service)]
PLACE_SERVICE_DEP = Annotated[PlaceService, Depends(get_place_service)]
SettingsDep = Annotated[Settings, Depends(get_settings_from_lifespan)]