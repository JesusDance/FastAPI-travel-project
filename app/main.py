from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import AsyncClient
from sqlmodel import SQLModel

from app.db import engine
from app.place import router as place_router
from app.projects import router as project_router
from app.users import router as user_router


def create_db_and_tables():
    SQLModel.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    app.state.httpx_client = AsyncClient(http2=True)
    yield
    await app.state.httpx_client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(project_router)
app.include_router(place_router)
app.include_router(user_router)


@app.get("/")
def get_root():
    return {"message": "Hello from backend!"}
