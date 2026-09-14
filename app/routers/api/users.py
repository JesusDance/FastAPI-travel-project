from typing import Annotated, Any

from fastapi import APIRouter, Body, status
from fastapi.exceptions import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

from app.core.security import verify_password, create_access_token, \
    get_password_hash
from app.db.session import SessionDep
from app.models.user import User
from app.routers.dependencies import SettingsDep
from app.schemas.token import Token
from app.schemas.user import UserSignUp, UserLogin, UserOut

router = APIRouter(prefix="/register", tags=["register"])
USER_SIGN_UP = Annotated[UserSignUp, Body()]
USER_LOGIN = Annotated[UserLogin, Body()]


@router.post("/", response_model=UserOut, status_code=201)
async def register_user(session: SessionDep, user: USER_SIGN_UP) -> Any:
    existing_user = await session.scalar(
        select(User).where(
            or_(User.username == user.username, User.email == user.email)
        )
    )

    if existing_user:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Username or email already exists"
        )

    user_db = User(
        **user.model_dump(exclude={"password"}),
        password=get_password_hash(user.password)
    )
    session.add(user_db)
    try:
        await session.commit()
        await session.refresh(user_db)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Username or email already exists"
        )

    return user_db


@router.post("/login", response_model=Token)
async def login_user(session: SessionDep, user: USER_LOGIN, settings: SettingsDep) -> Any:
    existing_user = await session.scalar(
        select(User).where(User.username == user.username)
        )

    if not existing_user or not verify_password(user.password, existing_user.password):
        raise HTTPException(401, "Invalid username or password")

    token = create_access_token(existing_user.id, settings)

    return {"access_token": token, "token_type": "Bearer"}
