from pydantic import field_validator

from app.schemas.project import ProjectCreate


class ProjectCreateForm(ProjectCreate):
    @field_validator("description", "start_date", mode="before")
    @classmethod
    def empty_fields_to_none(cls, value):
        return None if value == "" else value



