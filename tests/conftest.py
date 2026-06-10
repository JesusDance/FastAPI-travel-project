import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from asgi_lifespan import LifespanManager
from app.config import TestingConfig
from app.db import get_session
from app.main import app
from app.models import Project, Place, User
from app.security import get_password_hash
from pytest_httpx import HTTPXMock
from httpx import AsyncClient, ASGITransport

settings = TestingConfig()

test_engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)


def override_get_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="module")
def create_test_db():
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        default_user = User(
            username="Bob",
            password=get_password_hash("12345678"),
            email="bob123@gmail.com",
            projects=[],
        )
        second_user = User(
            username="Steve",
            password=get_password_hash("12345678"),
            email="steve123@gmail.com",
            projects=[],
        )
        session.add_all([default_user, second_user])
        session.commit()

        project1 = Project(
            name="test_project",
            description="some_description",
            is_completed=False,
            places=[],
            user_id=default_user.id,
        )
        project2 = Project(
            name="test_project2",
            description="some_description2",
            is_completed=False,
            places=[],
            user_id=second_user.id,
        )
        session.add_all([project1, project2])
        session.commit()

        place1 = Place(
            notes="",
            is_visited=False,
            project_id=project1.id,
            external_id=43365,
            title="Vase",
            user_id=default_user.id,
        )
        place2 = Place(
            notes="",
            is_visited=False,
            project_id=project2.id,
            external_id=44769,
            title="Melchior, from the Three Magi",
            user_id=second_user.id,
        )
        session.add_all([place1, place2])
        session.commit()

        yield
        SQLModel.metadata.drop_all(test_engine)


@pytest_asyncio.fixture
async def mock_artic_artwork(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        json={"data": {"title": "some place"}},
        http_version="HTTP/2.0",
        is_optional=True,
        is_reusable=True,
    )


@pytest_asyncio.fixture(scope="module")
async def test_client(create_test_db):
    app.dependency_overrides[get_session] = override_get_session
    async with LifespanManager(app) as manager:
        async with AsyncClient(
                transport=ASGITransport(manager.app),
                base_url="http://test",
                follow_redirects=True,
                http2=True) as client:
            yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client_api(create_test_db, mock_artic_artwork):
    app.dependency_overrides[get_session] = override_get_session
    async with LifespanManager(app) as manager:
        async with AsyncClient(
                transport=ASGITransport(manager.app),
                base_url="http://test",
                follow_redirects=True,
                http2=True) as client:
            await client.get("https://api.artic.edu/api/v1/artworks/12124")
            yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module")
async def default_user_token(test_client):
    response = await test_client.post(
        "/register/login/",
        json={"username": "Bob", "password": "12345678", "email": "bob123@gmail.com"},
    )
    json_response = response.json()
    yield json_response["access_token"]


@pytest_asyncio.fixture(scope="module")
async def second_user_token(test_client):
    response = await test_client.post(
        "/register/login/",
        json={
            "username": "Steve",
            "password": "12345678",
            "email": "steve123@gmail.com",
        },
    )
    json_response = response.json()
    yield json_response["access_token"]
