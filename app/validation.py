from fastapi import HTTPException
from sqlmodel import select

from app.db import SessionDep
from app.models import Project, Place


def check_places_limit(session: SessionDep, project_id: int):
    count = session.exec(select(Place).where(Place.project_id == project_id)).all()

    if len(count) >= 10:
        raise HTTPException(400, "Max 10 places per project")


def update_project_completion(session: SessionDep, project: Project):
    places = session.exec(select(Place).where(Place.project_id == project.id)).all()

    if places and all(p.is_visited for p in places):
        project.is_completed = True
    else:
        project.is_completed = False

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "updated", "project_completed": project.is_completed}
