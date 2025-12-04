from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from project.core.config import settings
from typing import AsyncGenerator

# Создаём движок
engine = create_async_engine(settings.postgres_url, echo=False)

# Фабрика сессий
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Зависимость для FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session