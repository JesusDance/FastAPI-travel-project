from fastapi import HTTPException
from sqlalchemy import select

from app.db import SessionDep
from app.models import Project, Place


async def check_places_limit(session: SessionDep, project_id: int):
    count = (await session.scalars(select(Place).where(Place.project_id == project_id))).all()

    if len(count) >= 10:
        raise HTTPException(400, "Max 10 places per project")


async def update_project_completion(session: SessionDep, project: Project):
    places = (await session.scalars(select(Place).where(Place.project_id == project.id))).all()

    if places and all(p.is_visited for p in places):
        project.is_completed = True
    else:
        project.is_completed = False

    session.add(project)
    await session.flush() # відправити зміни в БД у межах поточної transaction, але ще не завершувати transaction
    return {"status": "updated", "project_completed": project.is_completed}
