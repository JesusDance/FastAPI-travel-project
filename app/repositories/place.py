from typing import Any

from sqlalchemy import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Place, Project
from app.schemas.place import PlaceUpdate


class PlaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int, project_id: int) -> Any:
        return (
            await self.session.scalars(
                select(Place).where(
                    Place.user_id == user_id, Place.project_id == project_id
                )
            )
        ).all()

    async def get_all_paginated(
            self,
            user_id: int,
            project_id: int,
            offset: int,
            limit: int,
            is_visited: bool | None,
            search: str | None,
    ) -> Any:
        stmt = select(Place).where(
            Place.user_id == user_id, Place.project_id == project_id
        ).order_by(Place.id.desc()).offset(offset).limit(limit)

        if is_visited is not None:
            stmt = stmt.where(Place.is_visited == is_visited)

        if search:
            stmt = stmt.where(Place.title.ilike(f"%{search}%"))

        return (await self.session.scalars(stmt)).all()

    async def get_one(self, user_id: int, project_id: int, place_id: int) -> Place:
        return await self.session.scalar(
            select(Place)
            .join(Project, Place.project_id == Project.id)
            .where(
                Project.user_id == user_id,
                Project.id == project_id,
                Place.id == place_id,
            )
        )

    async def get_one_by_external_id(
        self, user_id: int, project_id: int, external_id: int
    ) -> Place:
        return await self.session.scalar(
            select(Place).where(
                Place.user_id == user_id,
                Place.project_id == project_id,
                Place.external_id == external_id,
            )
        )

    async def create(
        self,
        user_id: int,
        project_id: int,
        external_id: int,
        title: str,
    ) -> Place:

        place = Place(
            user_id=user_id,
            project_id=project_id,
            external_id=external_id,
            title=title,
        )

        self.session.add(place)
        return place

    async def update(
        self, user_id: int, project_id: int, place_id: int, place_schema: PlaceUpdate
    ) -> None:
        await self.session.scalar(
            update(Place)
            .where(
                Place.user_id == user_id,
                Place.project_id == project_id,
                Place.id == place_id,
            )
            .values(**place_schema)
            .returning(Place)
        )
