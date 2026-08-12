# FastAPI Travel Project

Async REST API for managing travel projects and places to visit.

This project demonstrates backend development with FastAPI, async SQLAlchemy, PostgreSQL, Redis, JWT authentication, 
Alembic migrations, Docker, external API integrations, and automated testing.

## Features

- User registration and JWT authentication
- Create, read, update, and delete travel projects
- Add and manage places inside projects
- Pagination, filtering, and search
- Add notes to places
- Mark places as visited
- Automatically complete projects when all places are visited
- Redis caching and IP-based rate limiting
- Integration with the Art Institute of Chicago API
- Async database and HTTP requests
- Docker support
- Async tests with pytest

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- SQLite for tests
- Alembic
- Redis
- httpx
- Pydantic v2
- JWT
- Argon2 password hashing
- Docker
- pytest and pytest-asyncio

## Architecture
The project uses a layered architecture:
Router → Service → Repository → Database

## Database migrations
1. alembic revision --autogenerate -m "init"
2. alembic upgrade head

# Installation

## 1. Clone repo
1. git clone https://github.com/JesusDance/FastAPI-travel-project.git
2. cd FastAPI-travel-project

## 2. Create virtual environment
1. python -m venv .venv
2. source .venv/bin/activate  # Linux/Mac
3. .venv\Scripts\activate     # Windows


## 3. Install dependencies
pip install -r requirements.txt

## 4. Run app
uvicorn app.main:app --reload


App runs at:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs


# API Endpoints

## Projects

- POST    /projects
- GET     /projects
- GET     /projects/{id}
- PATCH   /projects/{id}
- DELETE  /projects/{id}

## Places

- POST    /projects/{project_id}/places
- GET     /projects/{project_id}/places
- GET     /projects/{project_id}/places/{place_id}
- PATCH   /projects/{project_id}/places/{place_id}


## Create project

POST /projects

{
  "name": "Test for Junior",
  "description": "Spring travel plan",
}

## Get projects

List projects:

GET /projects/?offset=0&limit=5

Supported query parameters:
1. offset
2. limit
3. is_completed
4. search

## Get project

GET /projects/{project_id}

## Update project

PATCH /projects/{project_id}

{
  "name": "some text",
  "description": "some text"
}

## Add place

POST /projects/1/places

{
  "external_id": 23478
}

## Get place

GET /projects/{project_id}/places/{place_id}

## Update place

PATCH /projects/{project_id}/places/{place_id}

{
  "notes": "Must visit at sunset",
  "is_visited": true
}

# Docker

1. docker build -t travel-api .
2. docker run -p 8000:8000 travel-api
