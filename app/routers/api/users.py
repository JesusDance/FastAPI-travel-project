from __future__ import annotations
from typing import Annotated, Any, TYPE_CHECKING

from fastapi import APIRouter, Body, Form, status
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from app.db.session import SessionDep
from app.core.templates import templates
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserIn, UserOut
from app.core.security import verify_password, create_access_token, \
    get_password_hash
from app.api.dependencies import SettingsDep

router = APIRouter(prefix="/register", tags=["register"])
USER = Annotated[UserIn, Form()]


@router.post("/signin", response_model=UserOut, response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
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


@router.post("/login", response_model=Token, response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def login_user(
        request: Request,
        session: SessionDep,
        user: USER,
        settings: SettingsDep,
) -> Any:
    existing_user = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if not existing_user or not verify_password(user.password, existing_user.password):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Invalid username or password"}
        )

    token = create_access_token(existing_user.id, settings)

    return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"access_token": token, "token_type": "Bearer"}
        )
