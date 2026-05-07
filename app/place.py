from typing import List, Any

from fastapi import HTTPException, APIRouter
from sqlmodel import select

from app.db import SessionDep
from app.models import Place
from app.projects import TOKEN_DEP
from app.projects import (
    get_project,
    check_places_limit,
    fetch_place_from_api,
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

    title = fetch_place_from_api(place.external_id)

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


@router.get("/{project_id}/places", response_model=List[PlaceRead])
def get_places(session: SessionDep, project_id: int, token: TOKEN_DEP) -> Any:
    user_id = decode_token(token)
    return session.exec(
        select(Place).where(Place.project_id == project_id, Place.user_id == user_id)
    ).all()


@router.get("/{project_id}/places/{place_id}", response_model=PlaceRead)
def get_place(
    session: SessionDep, project_id: int, place_id: int, token: TOKEN_DEP
) -> Any:
    user_id = decode_token(token)
    place = session.get(Place, place_id)

    if not place or place.project_id != project_id:
        raise HTTPException(404, "Place not found")

    if not place.user_id == user_id:
        raise HTTPException(401, "You don't have access to this place")

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
    place_db = get_place(session, project_id, place_id, token)

    if not place_db:
        raise HTTPException(404, "Place not found")

    if not place_db.user_id == user_id:
        raise HTTPException(401, "You don't have access to this place")

    update_data = place.model_dump(exclude_unset=True)
    place_db.sqlmodel_update(update_data)

    session.add(place_db)
    session.commit()
    session.refresh(place_db)

    project = get_project(session, project_id, token)
    update_project_completion(session, project)

    return place_db
