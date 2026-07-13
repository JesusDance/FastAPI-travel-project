from typing import Annotated

from fastapi import Depends, Body
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient
from redis.asyncio import Redis

from app.client import get_httpx_client
from app.schemas import ProjectUpdate
from cache.redis_client import get_redis_client

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/register/login")

TOKEN_DEP = Annotated[str, Depends(oauth2_schema)]
UPDATE_PROJECT = Annotated[ProjectUpdate, Body()]
CLIENT = Annotated[AsyncClient, Depends(get_httpx_client)]
REDIS_CLIENT = Annotated[Redis, Depends(get_redis_client)]

