from typing import List, Optional
from datetime import date

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint


class BaseProject(SQLModel):
    name: str = Field(min_length=3, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    start_date: Optional[date] = None


class BasePlace(SQLModel):
    notes: Optional[str] = Field(default=None, max_length=255)
    is_visited: bool = Field(default=False)


class Project(BaseProject, table=True):
    __tablename__ = "project"

    id: int | None = Field(default=None, primary_key=True)
    is_completed: bool = Field(default=False)

    places: List["Place"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete"}
    )


class Place(BasePlace, table=True):
    __tablename__ = "place"

    __table_args__ = (
        UniqueConstraint("project_id", "external_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    external_id: int = Field(index=True)
    title: str
    project: Optional[Project] = Relationship(back_populates="places")





