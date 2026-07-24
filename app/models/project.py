from __future__ import annotations

from datetime import date
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.place import Place


class Project(Base):
    __tablename__ = "project"

    __table_args__ = (UniqueConstraint("user_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(
        default= date.today, nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(default=False)

    places: Mapped[List["Place"]] = relationship(
        back_populates="project",
        cascade="all, delete",
        lazy="selectin",
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[Optional[User]] = relationship(back_populates="projects")