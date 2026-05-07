from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

sqlite_url = "sqlite:///db.sqlite"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
