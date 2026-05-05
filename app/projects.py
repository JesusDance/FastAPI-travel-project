from typing import List, Any

import requests
from fastapi import HTTPException, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.db import SessionDep
from app.models import Project, Place
from app.schemas import ProjectCreate, ProjectUpdate, ProjectRead

router = APIRouter(prefix='/projects', tags=['projects'])

ARTIC_API_URL = "https://api.artic.edu/api/v1/artworks"

def fetch_place_from_api(external_id: int) -> str:
    url = f"{ARTIC_API_URL}/{external_id}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Place not found in external API")

    data = response.json().get("data")
    if not data:
        raise HTTPException(status_code=404, detail="Invalid response from API")

    return data.get("title", "Unknown")


def check_places_limit(session: SessionDep, project_id: int):
    count = session.exec(
        select(Place).where(Place.project_id == project_id)
    ).all()

    if len(count) >= 10:
        raise HTTPException(status_code=400, detail="Max 10 places per project")


def update_project_completion(session: SessionDep, project: Project):
    places = session.exec(
        select(Place).where(Place.project_id == project.id)
    ).all()

    if places and all(p.is_visited for p in places):
        project.is_completed = True
    else:
        project.is_completed = False

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "updated", "project_completed": project.is_completed}


@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(session: SessionDep, data: ProjectCreate) -> Any:
    project = Project(
        name=data.name,
        description=data.description,
        start_date=data.start_date
    )
    session.add(project)
    session.flush()

    for place in data.places:
        check_places_limit(session, project.id)

        title = fetch_place_from_api(place.external_id)

        existing = session.exec(
            select(Place).where(
                Place.project_id == project.id,
                Place.external_id == place.external_id
            )
        ).first()

        if existing:
            raise HTTPException(status_code=409, detail="Place already exists in project")

        db_place = Place(
            project_id=project.id,
            external_id=place.external_id,
            title=title
        )

        session.add(db_place)

    session.commit()
    session.refresh(project)
    return project


@router.get("/", response_model=List[ProjectRead])
def get_projects(session: SessionDep):
    return session.exec(select(Project)).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(session: SessionDep, project_id: int):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(session: SessionDep, project_id: int, data: ProjectUpdate):
    project = get_project(session, project_id)

    update_data = data.model_dump(exclude_unset=True)
    project.sqlmodel_update(update_data)

    session.add(project)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(422, detail=f"{e.orig}")
    session.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(session: SessionDep, project_id: int):
    project = get_project(session, project_id)

    visited_exists = session.exec(
        select(Place).where(
            Place.project_id == project_id,
            Place.is_visited == True
        )
    ).first()

    if visited_exists:
        raise HTTPException(400, "Cannot delete project with visited places")

    session.delete(project)
    session.commit()
    return {"detail": "Project deleted"}