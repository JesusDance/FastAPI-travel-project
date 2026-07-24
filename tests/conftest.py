import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from pytest_httpx import HTTPXMock
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import get_session
from app.main import app
from app.models import Project, Place, User, Base
from app.core.security import get_password_hash
from cache.redis_client import get_redis_client
from tests.fake_redis import override_redis_client

test_engine = create_async_engine(
    "sqlite+aiosqlite:///test.db", connect_args={"check_same_thread": False}
)

test_async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False)


async def override_get_session():
    async with test_async_session() as a_session:
        yield a_session


@pytest_asyncio.fixture(scope="module")
async def create_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


    async with test_async_session() as session:
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
        await session.flush()

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
        await session.flush()

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
        await session.commit()

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def mock_artic_artwork(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.artic.edu/api/v1/artworks/12124",
        json={"data": {"title": "some place"}},
        http_version="HTTP/2.0",
        is_optional=True,
    )


@pytest_asyncio.fixture(scope="module")
async def test_client(create_test_db):
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis_client] = override_redis_client
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
    app.dependency_overrides[get_redis_client] = override_redis_client
    async with LifespanManager(app) as manager:
        async with AsyncClient(
                transport=ASGITransport(manager.app),
                base_url="http://test",
                follow_redirects=True,
                http2=True) as client:
            yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module")
async def default_user_token(test_client):
    response = await test_client.post(
        "/register/login/",
        json={"username": "Bob",
              "password": "12345678",
              "email": "bob123@gmail.com",
        },
    )
    json_response = response.json()
    yield json_response["access_token"]


@pytest_asyncio.fixture(scope="module", autouse=True)
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
