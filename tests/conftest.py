import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel

from app.main import app
from app.config import TestingConfig
from app.db import get_session
from app.models import Project, Place, User
from app.security import get_password_hash

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
            projects=[]
        )
        session.add_all([default_user, second_user])
        session.commit()

        project1 = Project(
            name="test_project",
            description="some_description",
            is_completed=False,
            places=[],
            user_id=default_user.id
        )
        project2 = Project(
            name="test_project2",
            description="some_description2",
            is_completed=False,
            places=[],
            user_id=second_user.id
        )
        session.add_all([project1, project2])
        session.commit()

        place1 = Place(
            notes="",
            is_visited=False,
            project_id=project1.id,
            external_id=43285,
            title="some_title",
            user_id=default_user.id
        )
        place2 = Place(
            notes="",
            is_visited=False,
            project_id=project2.id,
            external_id=31563,
            title="some_title",
            user_id=second_user.id
        )
        session.add_all([place1, place2])
        session.commit()

        yield
        SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="module")
def test_client(create_test_db):
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def default_user_token(test_client):
    response = test_client.post(
        "/register/login/",
        json={
            "username": "Bob",
            "password": "12345678",
            "email": "bob123@gmail.com"
        },
    )
    json_response = response.json()
    yield json_response["access_token"]


@pytest.fixture(scope="module")
def second_user_token(test_client):
    response = test_client.post(
        "/register/login/",
        json={
            "username": "Steve",
            "password": "12345678",
            "email": "steve123@gmail.com"
        },
    )
    json_response = response.json()
    yield json_response["access_token"]