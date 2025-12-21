"""
Modelo de Página Web - Targets para auditoría.
Representa sitios web que serán analizados por el bot.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class WebPage(SQLModel, table=True):
    """
    Página web objetivo para auditoría SEO.
    Cada usuario puede tener múltiples targets.
    """
    __tablename__ = "web_pages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relación con el usuario
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Datos del target
    url: str = Field(index=True, description="URL completa del sitio a auditar")
    name: Optional[str] = Field(default=None, description="Nombre descriptivo del sitio")

    # Instrucciones de navegación (opcional)
    instructions: Optional[str] = Field(
        default=None,
        description="Instrucciones de navegación antes de auditar (ej. clicks, logins)"
    )

    # Stack tecnológico (opcional)
    tech_stack: Optional[str] = Field(
        default=None,
        description="Tecnologías detectadas o declaradas (ej. WordPress, React)"
    )

    # Metadatos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    #created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    #updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "name": "Mi Sitio Web",
                "instructions": "Click en 'Aceptar cookies' si aparece",
                "tech_stack": "WordPress + WooCommerce"
            }
        }

