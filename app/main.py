from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.db import engine
from app.place import router as place_router
from app.projects import router as project_router
from app.users import router as user_router


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(project_router)
app.include_router(place_router)
app.include_router(user_router)


@app.get("/")
def get_root():
    return {"message": "Hello from backend!"}
