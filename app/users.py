from typing import Annotated, Any

from fastapi import APIRouter, Body
from fastapi.exceptions import HTTPException
from sqlalchemy import select

from app.db import SessionDep
from app.models import User
from app.schemas import UserIn, UserOut, Token
from app.security import verify_password, create_access_token, \
    get_password_hash

router = APIRouter(prefix="/register", tags=["register"])
USER = Annotated[UserIn, Body()]


@router.post("/", response_model=UserOut, status_code=201)
async def register_user(session: SessionDep, user: USER) -> Any:
    existing_user = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if existing_user:
        raise HTTPException(400, "User already exists")
    if not user:
        raise HTTPException(422)

    user_db = User(
        **user.model_dump(exclude={"password"}),
        password=get_password_hash(user.password)
    )
    session.add(user_db)
    await session.commit()
    await session.refresh(user_db)

    return user_db


@router.post("/login", response_model=Token)
async def login_user(session: SessionDep, user: USER) -> Any:
    existing_user = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if not existing_user or not verify_password(user.password, existing_user.password):
        raise HTTPException(401, "Invalid username or password")

    token = create_access_token(existing_user.id)

    return {"access_token": token, "token_type": "Bearer"}
