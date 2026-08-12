from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio import Redis

from app.api.routers.place import router as place_router
from app.api.routers.project import router as project_router
from app.api.routers.users import router as user_router
from app.config.config import get_settings


#Запуст таблиць через алембік, тому опрокидувати в лафйспен не потрібно створення таблиць
# async def create_db_and_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI):
    app.state.httpx_client = AsyncClient(http2=True)
    app.state.settings = get_settings()
    app.state.redis_client = Redis.from_url(
        app.state.settings.REDIS_URL, decode_responses=True
    )
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
