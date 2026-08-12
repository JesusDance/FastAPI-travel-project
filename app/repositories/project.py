from datetime import date
from typing import Any

from sqlalchemy import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Place, Project
from app.schemas.project import ProjectUpdate


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int) -> Any:
        return (
            await self.session.scalars(
                select(Project).where(
                    Project.user_id == user_id).order_by(Project.id.desc())
            )
        ).all()

    async def get_all_paginated(
            self,
            user_id: int,
            offset: int,
            limit: int,
            is_completed: bool | None,
            search: str | None,
    ) -> Any:
        stmt = select(Project).where(
                        Project.user_id == user_id,
                    ).order_by(Project.name.desc()).offset(offset).limit(limit)

        if is_completed is not None:
            stmt = stmt.where(Project.is_completed == is_completed)

        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))
        return (await self.session.scalars(stmt)).all()

    async def get_one(self, user_id: int, project_id: int) -> Project:
        return await self.session.scalar(
            select(Project).where(
                Project.user_id == user_id, Project.id == project_id)
        )

    async def get_by_name(self, user_id: int, project_name: str) -> Project:
        return await self.session.scalar(
            select(Project).where(
                Project.name == project_name, Project.user_id == user_id
            )
        )

    async def get_project_with_visited_places(
        self, user_id: int, project_id: int
    ) -> Project:
        return await self.session.scalar(
            select(Project).join(Place, Project.id == Place.project_id)
            .where(
                Project.user_id == user_id,
                Project.id == project_id,
                Place.is_visited == True,
            )
        )

    async def create(
        self, user_id: int, name: str, description: str, start_date: date
    ) -> Project:
        params = {
            "name": name,
            "description": description,
            "start_date": start_date,
            "user_id": user_id,
            "places": [],
        }
        project = Project(**params)

        self.session.add(project)
        await self.session.flush()
        return project

    async def update(
        self, user_id: int, project_id: int, project_schema: ProjectUpdate
    ) -> Project:
        return await self.session.scalar(
            update(Project)
            .where(Project.user_id == user_id, Project.id == project_id)
            .values(**project_schema)
            .returning(Project)
        )

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
