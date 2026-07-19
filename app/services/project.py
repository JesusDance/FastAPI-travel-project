from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.client.client import ArticAPIClient
from app.config.config import settings
from app.repositories.place import PlaceRepository
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectRead, ProjectCreate

if TYPE_CHECKING:
    from app.schemas.project import ProjectUpdate


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_repository = ProjectRepository(session)
        self.place_repository = PlaceRepository(session)
        # опрокинув сюди похід в зовнішню api бо, не міг реалізувати цей рух на рівні ендпоїнта

    async def create(
        self, user_id, project_create: ProjectCreate, client: AsyncClient
    ) -> ProjectRead:
        exist_project = await self.project_repository.get_by_name(
            user_id, project_create.name
        )
        if exist_project:
            raise HTTPException(409, "Project already exists")

        api_client = ArticAPIClient(settings.ARTIC_API_URL, client)

        project_orm = await self.project_repository.create(
            **project_create.model_dump(mode="json", exclude={"places"}),
            user_id=user_id,
        )

        external_ids = [place.external_id for place in project_create.places]
        if len(external_ids) > 10:
            raise HTTPException(400, "Max 10 places per project")

        if len(external_ids) != len(set(external_ids)):
            raise HTTPException(409, "Place already exists in project")

        for place in project_create.places:
            title = await api_client.fetch_place_from_api(place.external_id)
            await self.place_repository.create(
                user_id, project_orm.id, place.external_id, title
            )

        await self.session.commit()
        await self.session.refresh(project_orm)
        return ProjectRead.model_validate(project_orm)


    async def get_all(self, user_id: int) -> list[ProjectRead]:
        projects = await self.project_repository.get_all(user_id)
        return [ProjectRead.model_validate(project) for project in projects]


    async def get_one(self, user_id: int, project_id: int) -> ProjectRead:
        project_orm = await self.project_repository.get_one(user_id, project_id)
        if not project_orm:
            raise HTTPException(404, "Project not found")

        return ProjectRead.model_validate(project_orm)


    async def get_with_visited_places(self, user_id: int, project_id: int) -> None:
        project_orm = await self.project_repository.get_project_with_visited_places(
            user_id, project_id
        )
        if project_orm:
            raise HTTPException(400, "Cannot delete project with visited places")


    async def update(
        self, user_id: int, project_id: int, project_update: ProjectUpdate
    ):
        if not project_update:
            raise HTTPException(422, "No fields to update")

        project = await self.project_repository.get_one(user_id, project_id)
        if not project:
            raise HTTPException(404, "Project not found")

        await self.project_repository.update(user_id, project_id, project_update)

        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(422, f"{e.orig}")

        return ProjectRead.model_validate(project)


    async def delete(self, user_id: int, project_id: int) -> None:
        project_orm = await self.project_repository.get_one(user_id, project_id)
        if not project_orm:
            raise HTTPException(404, "Project not found")

        await self.project_repository.delete(project_orm)
        await self.session.commit()


    async def update_project_completion(self, user_id, project_id: int) -> None:
        project_orm = await self.project_repository.get_one(user_id, project_id)
        places_orm = await self.place_repository.get_all(user_id, project_id)

        if project_orm and all(place.is_visited for place in places_orm):
            project_orm.is_completed = True
        else:
            project_orm.is_completed = False

        self.session.add(project_orm)
        await self.session.flush()
