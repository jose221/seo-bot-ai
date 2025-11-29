"""
Configuración de la base de datos con SQLModel y AsyncEngine.
"""
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings


# Motor asíncrono de SQLAlchemy
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Inicializa las tablas en la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia para obtener una sesión de base de datos"""
    async with async_session_maker() as session:
        yield session

