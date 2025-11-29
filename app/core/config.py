"""
Configuración central de la aplicación usando Pydantic Settings.
Lee variables de entorno y proporciona valores por defecto.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/seo_bot_db"

    # API Externa de Herandro
    HERANDRO_API_URL: str = "https://herandro-services-api.herandro.com.mx"

    # Seguridad
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Configuración de la aplicación
    PROJECT_NAME: str = "SEO Bot AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtener instancia de configuración"""
    return settings


