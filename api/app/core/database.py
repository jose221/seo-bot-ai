"""
Configuración de la base de datos con SQLModel y AsyncEngine.
Provee una capa de abstracción para conexiones asíncronas y síncronas.
"""
from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator, Generator, Optional
from contextlib import contextmanager, asynccontextmanager

from app.core.config import get_settings

# Importar todos los modelos para que SQLModel los registre
from app.models import (  # noqa: F401
    user,
    webpage,
    audit,
    audit_comparison,
    audit_schema_review,
    audit_url_validation,
    url_validation_comment,
    rich_results_report,
    structured_validation_task,
    structured_validation_comment,
)


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
                # Termina automáticamente sesiones idle-in-transaction tras 60s
                # para evitar que conexiones huérfanas bloqueen migraciones futuras.
                connect_args={
                    "server_settings": {
                        "idle_in_transaction_session_timeout": "60000",  # ms
                    }
                },
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

    async def _terminate_blocking_connections(self) -> None:
        """
        Elimina conexiones idle-in-transaction y bloqueadas antes de ejecutar
        migraciones DDL, para evitar que transacciones huérfanas (de reinicios
        abruptos del servidor) impidan adquirir los locks necesarios.
        """
        async with self.async_engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid != pg_backend_pid()
                  AND (
                      state = 'idle in transaction'
                      OR (state = 'active' AND wait_event_type = 'Lock')
                  )
                  AND query_start < NOW() - INTERVAL '10 seconds'
            """))
            await conn.commit()
            terminated = result.rowcount
            if terminated:
                print(f"🧹 Terminadas {terminated} conexiones bloqueadas antes de migraciones")

    async def init_db(self):
        """Inicializa las tablas en la base de datos"""
        # Limpiar conexiones huérfanas antes de ejecutar DDL
        await self._terminate_blocking_connections()

        async with self.async_engine.begin() as conn:
            # lock_timeout: si no consigue el lock en 15s, lanza error en lugar
            # de quedarse bloqueado indefinidamente.
            await conn.execute(text("SET LOCAL lock_timeout = '15s'"))
            await conn.run_sync(SQLModel.metadata.create_all)
            await conn.execute(text("""
                ALTER TABLE rich_results_reports
                ADD COLUMN IF NOT EXISTS analysis_findings JSONB
            """))
            await conn.execute(text("""
                ALTER TABLE rich_results_reports
                ADD COLUMN IF NOT EXISTS validate_google BOOLEAN NOT NULL DEFAULT TRUE
            """))
            await conn.execute(text("""
                ALTER TABLE rich_results_reports
                ADD COLUMN IF NOT EXISTS validate_schema_org BOOLEAN NOT NULL DEFAULT TRUE
            """))
            await conn.execute(text("""
                ALTER TABLE rich_results_reports
                ADD COLUMN IF NOT EXISTS google_validation_result JSONB
            """))
            await conn.execute(text("""
                ALTER TABLE rich_results_reports
                ADD COLUMN IF NOT EXISTS schema_org_validation_result JSONB
            """))
            await conn.execute(text("""
                ALTER TABLE structured_validation_tasks
                ADD COLUMN IF NOT EXISTS browser_mode_code VARCHAR(80)
            """))

    @asynccontextmanager
    async def async_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sesiones asíncronas"""
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

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
