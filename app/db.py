from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, \
    async_sessionmaker

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_session():
    async with async_session() as a_session:
        yield a_session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
