from datetime import date

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str


class PlaceCreate(BaseModel):
    external_id: int


class PlaceUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=255)
    is_visited: bool | None = None


class PlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    title: str
    notes: str | None
    is_visited: bool


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    description: str | None = Field(default=None, min_length=3, max_length=255)
    start_date: date | None = Field(default=None)
    # для кожного нового ProjectCreate створиться новий порожній список, бо default список може шаритись між інстансами.
    # Pydantic часто захищає від цього, але правильний стиль все одно default_factory
    places: list[PlaceCreate] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=50)
    description: str | None = Field(default=None, min_length=3, max_length=255)
    start_date: date | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    places: list[PlaceRead]
    is_completed: bool


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=255)
    email: EmailStr | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
