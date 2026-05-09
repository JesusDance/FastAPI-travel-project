from datetime import date

from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field

from app.models import BaseUser, BaseProject, BasePlace


class Token(BaseModel):
    access_token: str
    token_type: str


class PlaceCreate(BasePlace):
    external_id: int


class PlaceUpdate(BasePlace):
    notes: str | None = Field(default=None, max_length=255)
    is_visited: bool | None = None


class PlaceRead(SQLModel):
    id: int
    external_id: int
    title: str
    notes: str | None
    is_visited: bool


class ProjectCreate(BaseProject):
    places: list[PlaceCreate] = []


class ProjectUpdate(BaseProject):
    name: str | None = Field(default=None, min_length=3, max_length=50)
    description: str | None = Field(default=None, min_length=3, max_length=255)
    start_date: date | None = None


class ProjectRead(SQLModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    places: list[PlaceRead]
    is_completed: bool


class UserIn(BaseUser):
    email: EmailStr | None = None


class UserOut(SQLModel):
    id: int
    username: str
    email: EmailStr
    projects: list[ProjectRead] | None = None
