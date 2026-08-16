from pydantic import BaseModel, Field


class PlaceSuggestion(BaseModel):
    name: str
    category: str
    reason: str
    estimated_visit_minutes: int


class Suggestions(BaseModel):
    project_name: str
    suggestions: list[PlaceSuggestion]


class Preferences(BaseModel):
    preferences: str = Field(min_length=1, max_length=50)
    days: int = Field(default=1, ge=1, le=30)
