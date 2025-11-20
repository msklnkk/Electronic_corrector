from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from .settings import Settings


engine = create_async_engine(Settings().DATABASE_URL, echo=Settings().DATABASE_DEBUG)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

engine_sync = create_engine(Settings().DATABASE_URL_SYNC)

def get_session():
    with Session(engine_sync) as session:
        yield session


