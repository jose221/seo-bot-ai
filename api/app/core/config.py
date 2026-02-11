"""
Configuración central de la aplicación usando Pydantic Settings.
Lee variables de entorno y proporciona valores por defecto.
"""
from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Configuración de Base de Datos (componentes separados)
    DB_DRIVER: str = "postgresql"
    DB_ASYNC_DRIVER: str = "asyncpg"
    DB_SYNC_DRIVER: str = "psycopg2"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "seo_bot_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # API Externa de Herandro
    HERANDRO_API_URL: str = "https://herandro-services-api.herandro.com.mx"

    # Seguridad
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Configuración de la aplicación
    PROJECT_NAME: str = "SEO Bot AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    # Storage
    # Ruta relativa al directorio de ejecución (ej: /app/storage en Docker, ./storage en local)
    STORAGE_PATH: str = "storage"
    STORAGE_URL_PREFIX: str = "/storage"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """Construir URL de conexión asíncrona"""
        return (
            f"{self.DB_DRIVER}+{self.DB_ASYNC_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Construir URL de conexión síncrona (para background tasks)"""
        return (
            f"{self.DB_DRIVER}+{self.DB_SYNC_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL(self) -> str:
        """URL por defecto (asíncrona)"""
        return self.DATABASE_URL_ASYNC


# Instancia global de configuración
@lru_cache()
def get_settings() -> Settings:
    """Obtener instancia de configuración (cached)"""
    return Settings()


settings = get_settings()


