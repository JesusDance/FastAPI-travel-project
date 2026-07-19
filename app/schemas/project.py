from datetime import date

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.place import PlaceCreate, PlaceRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    description: str | None = Field(default=None, min_length=3, max_length=255)
    start_date: date | None = Field(default=None)
    # для кожного нового ProjectCreate створиться новий порожній список, бо default список може шаритись між інстансами.
    # Pydantic часто захищає від цього, але правильний стиль все одно default_factory
    places: list[PlaceCreate] = Field(default_factory=list)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    places: list[PlaceRead]
    is_completed: bool


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=50)
    description: str | None = Field(default=None, min_length=3, max_length=255)
    start_date: date | None = None