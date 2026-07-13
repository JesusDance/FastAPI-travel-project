from datetime import date
from typing import List, Optional

from sqlalchemy import UniqueConstraint, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    projects: Mapped[List["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "project"

    __table_args__ = (UniqueConstraint("user_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(nullable=True)
    is_completed: Mapped[bool] = mapped_column(default=False)

    places: Mapped[List["Place"]] = relationship(
        back_populates="project", cascade="all, delete", lazy="selectin"
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[Optional[User]] = relationship(back_populates="projects")


class Place(Base):
    __tablename__ = "place"

    __table_args__ = (UniqueConstraint("project_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    title: Mapped[str]
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_visited: Mapped[bool] = mapped_column(default=False)

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    project: Mapped[Optional[Project]] = relationship(back_populates="places")
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
