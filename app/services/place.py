from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.client.client import ArticAPIClient
from app.config.config import Settings
from app.repositories.place import PlaceRepository
from app.repositories.project import ProjectRepository
from app.schemas.place import PlaceRead, PlaceCreate, PlaceUpdate


class PlaceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.place_repository = PlaceRepository(session)
        self.project_repository = ProjectRepository(session)


    async def create(
        self,
        user_id: int,
        project_id: int,
        place_schema: PlaceCreate,
        client: AsyncClient,
        settings: Settings,
    ) -> PlaceRead:
        project_orm = await self.project_repository.get_one(user_id, project_id)

        if not project_orm:
            raise HTTPException(404, "Project not found")

        places_orm = await self.place_repository.get_all(user_id, project_id)

        if len(places_orm) >= 10:
            raise HTTPException(400, "Max 10 places per project")

        existing_place = await self.place_repository.get_one_by_external_id(
            user_id, project_id, place_schema.external_id
        )
        if existing_place:
            raise HTTPException(409, "Place already exists in project")

        api_client = ArticAPIClient(settings.ARTIC_API_URL, client)

        title = await api_client.fetch_place_from_api(place_schema.external_id)
        params = {
            "user_id": user_id,
            "project_id": project_id,
            "external_id": place_schema.external_id,
            "title": title,
        }

        place_orm = await self.place_repository.create(**params)
        await self.session.commit()
        await self.session.refresh(place_orm)
        return PlaceRead.model_validate(place_orm)


    async def get_one(self, user_id: int, project_id: int, place_id: int) -> PlaceRead:
        place_orm = await self.place_repository.get_one(user_id, project_id, place_id)
        if not place_orm:
            raise HTTPException(404, "Place not found")

        return PlaceRead.model_validate(place_orm)


    async def get_all(self, user_id: int, project_id: int) -> list[PlaceRead]:
        places_orm = await self.place_repository.get_all(user_id, project_id)
        return [PlaceRead.model_validate(place) for place in places_orm]


    async def get_all_paginated(
            self,
            user_id: int,
            project_id: int,
            offset: int,
            limit: int,
            is_visited: bool | None,
            search: str | None,
    ) -> list[PlaceRead]:
        places_orm = await self.place_repository.get_all_paginated(
            user_id, project_id, offset, limit, is_visited, search
        )
        return [PlaceRead.model_validate(place) for place in places_orm]


    async def update(
        self, user_id: int, project_id: int, place_id: int, place_schema: PlaceUpdate
    ) -> PlaceRead:
        project_orm = await self.project_repository.get_one(user_id, project_id)

        if not project_orm:
            raise HTTPException(404, "Project not found")

        if not place_schema:
            raise HTTPException(404, "No fields to update")

        params = {
            "user_id": user_id,
            "project_id": project_id,
            "place_id": place_id,
            "place_schema": place_schema,
        }
        await self.place_repository.update(**params)

        places_orm = await self.place_repository.get_all(user_id, project_id)

        if places_orm and all(p.is_visited for p in places_orm):
            project_orm.is_completed = True
        else:
            project_orm.is_completed = False

        self.session.add(project_orm)
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(422, detail=f"{e.orig}")
        # session.refresh(place_db) проект вже повернен через update.returning()

        place_orm = await self.place_repository.get_one(user_id, project_id, place_id)
        return PlaceRead.model_validate(place_orm)
