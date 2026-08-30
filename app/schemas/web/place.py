from pydantic import field_validator

from app.schemas.place import PlaceUpdate


class PlaceUpdateForm(PlaceUpdate):
    @field_validator("notes", "is_visited", mode="before")
    @classmethod
    def empty_fields_to_none(cls, value):
        return None if value == "" else value
