from typing import Any, List

from sqlalchemy import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Place, Project
from app.schemas.project import ProjectUpdate
from datetime import date


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int) -> Any:
        return (
            await self.session.scalars(
                select(Project).where(Project.user_id == user_id)
            )
        ).all()

    async def get_one(self, user_id: int, project_id: int) -> Project:
        return await self.session.scalar(
            select(Project).where(Project.user_id == user_id, Project.id == project_id)
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
            select(Place).where(
                Project.user_id == user_id,
                Project.id == project_id,
                Place.project_id == project_id,
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
    ) -> None:
        await self.session.scalar(
            update(Project)
            .where(Project.user_id == user_id, Project.id == project_id)
            .values(**project_schema)
            .returning(Project)
        )

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
