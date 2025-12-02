"""
Configuración de la base de datos con SQLModel y AsyncEngine.
Provee una capa de abstracción para conexiones asíncronas y síncronas.
"""
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator, Generator, Optional
from contextlib import contextmanager, asynccontextmanager

from app.core.config import get_settings

# Importar todos los modelos para que SQLModel los registre
from app.models import user, webpage, audit  # noqa: F401


class DatabaseManager:
    """
    Gestor centralizado de conexiones a base de datos.
    Maneja tanto conexiones asíncronas como síncronas.
    """

    def __init__(self):
        self.settings = get_settings()
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine = None
        self._async_session_maker = None
        self._sync_session_maker = None

    @property
    def async_engine(self) -> AsyncEngine:
        """Motor asíncrono (lazy initialization)"""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.settings.DATABASE_URL_ASYNC,
                echo=self.settings.DEBUG,
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        return self._async_engine

    @property
    def sync_engine(self):
        """Motor síncrono para background tasks (lazy initialization)"""
        if self._sync_engine is None:
            # Configurar argumentos según el ambiente
            engine_kwargs = {
                'echo': self.settings.DEBUG,
                'pool_pre_ping': True,
            }

            # StaticPool para local (no acepta pool_size/max_overflow)
            if self.settings.ENVIRONMENT == "local":
                engine_kwargs['poolclass'] = StaticPool
            else:
                # Para otros ambientes, usar pool normal con configuración
                engine_kwargs['pool_size'] = 5
                engine_kwargs['max_overflow'] = 10

            self._sync_engine = create_engine(
                self.settings.DATABASE_URL_SYNC,
                **engine_kwargs
            )
        return self._sync_engine

    @property
    def async_session_maker(self):
        """Factory de sesiones asíncronas"""
        if self._async_session_maker is None:
            self._async_session_maker = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._async_session_maker

    @property
    def sync_session_maker(self):
        """Factory de sesiones síncronas"""
        if self._sync_session_maker is None:
            self._sync_session_maker = sessionmaker(
                self.sync_engine,
                class_=Session,
                expire_on_commit=False
            )
        return self._sync_session_maker

    async def init_db(self):
        """Inicializa las tablas en la base de datos"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def async_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sesiones asíncronas"""
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @contextmanager
    def sync_session_context(self) -> Generator[Session, None, None]:
        """Context manager para sesiones síncronas"""
        session = self.sync_session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def close(self):
        """Cerrar todas las conexiones"""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()


# === Funciones de compatibilidad con código existente ===

# Motor asíncrono (para código legacy)
engine = db_manager.async_engine

# Session maker asíncrono (para código legacy)
async_session_maker = db_manager.async_session_maker


async def init_db():
    """Inicializa las tablas en la base de datos"""
    await db_manager.init_db()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia para obtener una sesión de base de datos asíncrona"""
    async with db_manager.async_session_context() as session:
        yield session


def get_sync_session() -> Generator[Session, None, None]:
    """Dependencia para obtener una sesión de base de datos síncrona"""
    with db_manager.sync_session_context() as session:
        yield session


# === Funciones de utilidad ===

def get_database_url_sync() -> str:
    """Obtener URL de base de datos síncrona"""
    return get_settings().DATABASE_URL_SYNC


def get_database_url_async() -> str:
    """Obtener URL de base de datos asíncrona"""
    return get_settings().DATABASE_URL_ASYNC


