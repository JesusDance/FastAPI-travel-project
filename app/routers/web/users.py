from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from starlette.requests import Request

from app.core.security import verify_password, create_access_token, \
    get_password_hash
from app.core.templates import templates
from app.db.session import SessionDep
from app.models.user import User
from app.routers.dependencies import SettingsDep
from app.schemas.user import UserIn

router = APIRouter(prefix="/web", tags=["web"])
USER = Annotated[UserIn, Form()]


@router.post("/signup", response_class=HTMLResponse)
async def register_user(request: Request, session: SessionDep, user: USER) -> Any:
    existing_user = await session.scalar(
        select(User).where(User.username == user.username)
    )
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="registration/signup.html",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            context={"error": "Invalid username or password"}
        )

    user_db = User(
        **user.model_dump(exclude={"password"}),
        password=get_password_hash(user.password)
    )
    session.add(user_db)
    await session.commit()
    await session.refresh(user_db)

    return templates.TemplateResponse(
        request=request,
        status_code=status.HTTP_201_CREATED,
        name="registration/signup.html",
        context={"detail": f"User with {user_db.username} created!"}
    )


@router.post("/login", response_class=HTMLResponse)
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            name="registration/login.html",
            context={"error": "Invalid username or password"}
        )

    token = create_access_token(existing_user.id, settings)

    response = RedirectResponse(
        url="/web/profile",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return response


@router.post("/logout")
async def logout_user() -> Any:
    response = RedirectResponse(url="/web/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key="access_token",
        secure=False,
        httponly=True,
        samesite="lax",
    )
    return response