from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


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