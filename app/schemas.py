from datetime import date
from typing import Optional, List

from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel

from app.models import BaseUser


class Token(BaseModel):
    access_token: str
    token_type: str


class BaseProject(SQLModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None


class BasePlace(SQLModel):
    notes: Optional[str] = None
    is_visited: bool = False


class PlaceCreate(SQLModel):
    external_id: int


class PlaceUpdate(SQLModel):
    notes: Optional[str] = None
    is_visited: Optional[bool] = None


class PlaceRead(SQLModel):
    id: int
    external_id: int
    title: str
    notes: Optional[str]
    is_visited: bool


class ProjectCreate(BaseProject):
    places: List[PlaceCreate] = []


class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None


class ProjectRead(SQLModel):
    id: int
    name: str
    description: Optional[str]
    start_date: Optional[date]
    places: List[PlaceRead]
    is_completed: bool


class UserIn(BaseUser):
    email: EmailStr | None


class UserOut(SQLModel):
    id: int
    username: str
    email: EmailStr
    projects: List[ProjectRead] | None = None