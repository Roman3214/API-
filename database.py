from fastapi import Depends
from typing import Annotated, AsyncGenerator
from fastapi_users.db import SQLAlchemyUserDatabase 
from sqlalchemy import String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
import models
from config import settings

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=True,
    # pool_size=5,
    # max_overflow=10,
)

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
async_session_factory = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)

str_256 = Annotated[str, 256]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }

    repr_cols_num = 3
    repr_cols = tuple()
    
    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, models.User)