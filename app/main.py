from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google.genai import Client
from httpx import AsyncClient
from openai import AsyncOpenAI
from redis.asyncio import Redis
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from app.config.config import get_settings
from app.core.templates import templates
from app.routers.api.ai import router as api_router
from app.routers.api.place import router as place_router
from app.routers.api.project import router as project_router
from app.routers.api.users import router as user_router
from app.routers.dependencies import WEB_USER_ID_DEP, WebAuthRequired, \
    PROJECT_SERVICE_DEP
from app.routers.web.place import router as web_place_router
from app.routers.web.projects import router as web_project_router
from app.routers.web.users import router as web_user_router


#Запуст таблиць через алембік, тому опрокидувати в лафйспен не потрібно створення таблиць
# async def create_db_and_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI):
    app.state.httpx_client = AsyncClient(http2=True)
    app.state.settings = get_settings()
    app.state.redis_client = Redis.from_url(
        app.state.settings.REDIS_URL, decode_responses=True
    )
    app.state.openai = AsyncOpenAI(api_key=app.state.settings.OPENAI_API_KEY)
    app.state.gemini = Client(api_key=app.state.settings.GEMINI_API_KEY)
    yield
    await app.state.httpx_client.aclose()
    await app.state.redis_client.aclose()
    await app.state.openai.close()
    await app.state.gemini.aio.aclose()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path("static")), name="static")

app.include_router(project_router)
app.include_router(place_router)
app.include_router(user_router)
app.include_router(api_router)
app.include_router(web_user_router)
app.include_router(web_project_router)
app.include_router(web_place_router)

app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().SESSION_SECRET_KEY,
    session_cookie="flash_session",
    https_only=False,
)

@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_page(request: Request, user_id: WEB_USER_ID_DEP) -> Any:
    if user_id:
        message = request.session["user_in_session"] = "You are logged in"
        return templates.TemplateResponse(
            request=request,
            name="main/index.html",
            context={"user_in_session": message}
        )
    return templates.TemplateResponse(request=request, name="main/index.html")


@app.get("/web/signup", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_register_page(request: Request) -> Any:
    return templates.TemplateResponse(request=request, name="registration/signup.html")


@app.exception_handler(WebAuthRequired)
async def web_auth_required_handler(request: Request, _exc: WebAuthRequired):
    request.session["flash"] = "Please log in to continue"
    return RedirectResponse(
        url="/web/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get("/web/login", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_login_page(request: Request) -> Any:
    message = request.session.pop("flash", None)
    return templates.TemplateResponse(
        request=request,
        name="registration/login.html",
        context={"error": message},
    )


@app.get("/web/profile", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def profile(request: Request, user_id: WEB_USER_ID_DEP) -> Any:
    if user_id is None:
        raise WebAuthRequired
    return templates.TemplateResponse(
        request=request,
        name="main/profile.html",
        context={"user_in_session": user_id},
        )


@app.get(
    "/web/projects/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def create_project(request: Request, user_id: WEB_USER_ID_DEP) -> Any:
    if user_id is None:
        raise WebAuthRequired
    return templates.TemplateResponse(
        request=request,
        name="main/create_project.html",
    )


@app.get(
    "/web/projects/{project_id}/places/create",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def create_place(request: Request, user_id: WEB_USER_ID_DEP, project_id: int) -> Any:
    if user_id is None:
        raise WebAuthRequired
    return templates.TemplateResponse(
        request=request,
        name="main/create_place.html",
        context={"project_id": project_id},
    )


@app.get(
    "/web/projects/{project_id}/update",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK
)
async def projects_update(
        request: Request,
        user_id: WEB_USER_ID_DEP,
        project_id: int,
        project_service: PROJECT_SERVICE_DEP,
) -> Any:
    if user_id is None:
        raise WebAuthRequired

    project = await project_service.get_one(user_id, project_id)
    return templates.TemplateResponse(
        request=request,
        name="/main/update_project.html",
        context={"project": project},
    )


@app.get(
    "/web/projects/{project_id}/places/{place_id}/update",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def update_place(
    request: Request,
    user_id: WEB_USER_ID_DEP,
    project_id: int,
    place_id: int,
) -> Any:
    if user_id is None:
        raise WebAuthRequired
    return templates.TemplateResponse(
        request=request,
        name="main/update_place.html",
        context={
            "place_id": place_id,
            "project_id": project_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
) -> Any:
    if request.url.path == "/web/signup":
        return templates.TemplateResponse(
            request=request,
            name="registration/signup.html",
            context={"validation_error": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    if request.url.path == "/web/login":
        return templates.TemplateResponse(
            request=request,
            name="registration/login.html",
            context={"validation_error": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    if request.url.path == "/web/projects/create":
        return templates.TemplateResponse(
            request=request,
            name="main/create_project.html",
            context={"validation_error": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    project_id = request.path_params.get("project_id")
    place_id = request.path_params.get("place_id")
    if request.url.path == f"/web/projects/{project_id}/places/create":
        return templates.TemplateResponse(
            request=request,
            name="main/create_place.html",
            context={
                "project_id": project_id,
                "validation_error": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    if request.url.path == f"/web/projects/{project_id}/places/{place_id}/update":
        return templates.TemplateResponse(
            request=request,
            name="main/update_place.html",
            context={
                "place_id": place_id,
                "project_id": project_id,
                "validation_error": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder({"detail": exc.errors()})
    )
