from pydantic import BaseModel, Field, ConfigDict


class PlaceCreate(BaseModel):
    external_id: int


class PlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int
    title: str
    notes: str | None
    is_visited: bool


class PlaceUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=255)
    is_visited: bool | None = None