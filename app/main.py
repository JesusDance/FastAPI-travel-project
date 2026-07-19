from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio import Redis

from app.config.config import settings
from app.db.session import engine
from app.models import Base
from app.api.routers.place import router as place_router
from app.api.routers.project import router as project_router
from app.api.routers.users import router as user_router


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_db_and_tables()
    app.state.httpx_client = AsyncClient(http2=True)
    app.state.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield
    await app.state.httpx_client.aclose()
    await app.state.redis_client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(project_router)
app.include_router(place_router)
app.include_router(user_router)


@app.get("/")
def get_root():
    return {"message": "Hello from backend!"}
