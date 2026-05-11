from typing import Any

from fastapi import HTTPException, APIRouter
from sqlmodel import select

from app.db import SessionDep
from app.models import Place, Project
from app.projects import (
    TOKEN_DEP,
    ARTIC_API_URL,
    get_project,
    check_places_limit,
    ArticAPIClient,
    update_project_completion,
)
from app.schemas import PlaceUpdate, PlaceRead, PlaceCreate
from app.security import decode_token

router = APIRouter(prefix="/projects", tags=["place"])


@router.post("/{project_id}/places", response_model=PlaceRead, status_code=201)
def add_place(
    session: SessionDep, project_id: int, place: PlaceCreate, token: TOKEN_DEP
) -> Any:
    user_id = decode_token(token)

    check_places_limit(session, project_id)

    existing = session.exec(
        select(Place).where(
            Place.project_id == project_id, Place.external_id == place.external_id
        )
    ).first()

    if existing:
        raise HTTPException(409, "Place already exists in project")

    client = ArticAPIClient(ARTIC_API_URL)
    title = client.fetch_place_from_api(place.external_id)

    place = Place(
        project_id=project_id,
        external_id=place.external_id,
        title=title,
        user_id=user_id,
    )

    session.add(place)
    session.commit()
    session.refresh(place)

    return place


@router.get("/{project_id}/places", response_model=list[PlaceRead])
def get_places(session: SessionDep, project_id: int, token: TOKEN_DEP) -> Any:
    user_id = decode_token(token)
    project = session.exec(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(404, "Project not found")

    place = session.exec(select(Place).where(Place.project_id == project_id)).all()

    return place


@router.get("/{project_id}/places/{place_id}", response_model=PlaceRead)
def get_place(
    session: SessionDep, project_id: int, place_id: int, token: TOKEN_DEP
) -> Any:
    user_id = decode_token(token)
    project = session.exec(
        select(Project).where(Project.user_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(404, "Project not found")

    place = session.exec(
        select(Place).where(
            Place.user_id == user_id,
            Place.id == place_id,
            Place.project_id == project_id,
        )
    ).first()

    if not place:
        raise HTTPException(404, "Place not found")

    return place


@router.patch("/{project_id}/places/{place_id}", response_model=PlaceRead)
def update_place(
    session: SessionDep,
    project_id: int,
    place_id: int,
    place: PlaceUpdate,
    token: TOKEN_DEP,
) -> Any:

    user_id = decode_token(token)
    # place_db = get_place(session, project_id, place_id, token)
    place_db = session.exec(
        select(Place).where(
            Place.user_id == user_id,
            Place.project_id == project_id,
            Place.id == place_id,
        )
    ).first()

    if not place_db:
        raise HTTPException(404, "Place not found")

    update_data = place.model_dump(exclude_unset=True)
    place_db.sqlmodel_update(update_data)

    session.add(place_db)
    session.commit()
    session.refresh(place_db)

    project = get_project(session, project_id, token)
    update_project_completion(session, project)

    return place_db
