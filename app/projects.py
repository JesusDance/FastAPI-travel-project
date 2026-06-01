from typing import Any, Annotated

import requests
from fastapi import HTTPException, APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.db import SessionDep
from app.models import Project, Place
from app.schemas import ProjectCreate, ProjectUpdate, ProjectRead
from app.security import decode_token

router = APIRouter(prefix="/projects", tags=["projects"])
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/register/login")

ARTIC_API_URL = "https://api.artic.edu/api/v1/artworks"
TOKEN_DEP = Annotated[str, Depends(oauth2_schema)]
UPDATE_PROJECT = Annotated[ProjectUpdate, Body()]


class ArticAPIClient:
    def __init__(self, url):
        self.url = url

    def fetch_place_from_api(self, external_id: int) -> str:
        url = f"{self.url}/{external_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get("data")
            if not data:
                raise HTTPException(404, "Invalid response from API")
            return data.get("title", "Unknown")

        except requests.Timeout:
            raise HTTPException(504, "External API timeout")

        except requests.RequestException:
            raise HTTPException(404, "Place not found in external API")


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


@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(session: SessionDep, data: ProjectCreate, token: TOKEN_DEP) -> Any:
    user_id = decode_token(token)
    existing_project = session.exec(
        select(Project).where(Project.name == data.name, Project.user_id == user_id)
    ).first()

    if existing_project:
        raise HTTPException(409, "Project already exists")

    project = Project(**data.model_dump(exclude={"places"}), user_id=user_id)
    session.add(project)
    session.flush()

    client = ArticAPIClient(ARTIC_API_URL)

    count_external_ids = [place.external_id for place in data.places]

    if len(count_external_ids) > 10:
        raise HTTPException(400, "Max 10 places per project")

    if len(count_external_ids) != len(set(count_external_ids)):
        raise HTTPException(409, "Place already exists in project")

    for place in data.places:
        title = client.fetch_place_from_api(place.external_id)

        db_place = Place(
            project_id=project.id,
            external_id=place.external_id,
            title=title,
            user_id=user_id,
        )

        session.add(db_place)

    session.commit()
    session.refresh(project)
    return project


@router.get("/", response_model=list[ProjectRead])
def get_projects(session: SessionDep, token: TOKEN_DEP):
    user_id = decode_token(token)
    return session.exec(select(Project).where(Project.user_id == user_id)).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(session: SessionDep, project_id: int, token: TOKEN_DEP):
    user_id = decode_token(token)
    project = session.exec(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(404, "Project not found")
    update_project_completion(session, project)

    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    session: SessionDep, project_id: int, data: UPDATE_PROJECT, token: TOKEN_DEP
):
    user_id = decode_token(token)
    project = session.exec(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(404, "Project not found")

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
def delete_project(session: SessionDep, project_id: int, token: TOKEN_DEP):
    user_id = decode_token(token)
    project = session.exec(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(404, "Project not found")

    visited_exists = session.exec(
        select(Place).where(Place.project_id == project_id, Place.is_visited == True)
    ).first()

    if visited_exists:
        raise HTTPException(400, "Cannot delete project with visited places")

    session.delete(project)
    session.commit()
    return {"detail": "Project deleted"}
