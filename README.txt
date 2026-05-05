#FastAPI-travel-project

REST API for managing travel projects and places to visit.
Built with FastAPI, SQLModel, and integrates with the Art Institute of Chicago API.

##Features

- Create, update, delete travel projects
- Add places to projects
- Limit of 10 places per project
- Add notes to places
- Mark places as visited
- Auto-complete project when all places are visited
- SQLite database (auto-created on startup)

##Tech Stack

- FastAPI
- SQLModel
- SQLite
- Requests
- Alembic
- Dockerfile


#Installation

## 1. Clone repo

## 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows


## 3. Install dependencies
pip install -r requirements.txt

## 4. Run app
uvicorn app.main:app --reload


App runs at:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs


#API Endpoints

## Projects

POST    /projects
GET     /projects
GET     /projects/{id}
PATCH   /projects/{id}
DELETE  /projects/{id}

## Places

POST    /projects/{project_id}/places
GET     /projects/{project_id}/places
GET     /projects/{project_id}/places/{place_id}
PATCH   /projects/{project_id}/places/{place_id}


## Create project

POST /projects
{
  "name": "Test for Junior",
  "description": "Spring travel plan",
  "start_date": "2026-05-05"
}

## Add place

POST /projects/1/places
{
  "external_id": 23478
}

## Update place

PATCH /projects/1/places/1
{
  "notes": "Must visit at sunset",
  "is_visited": true
}

# Docker

docker build -t travel-api .
docker run -p 8000:8000 travel-api
