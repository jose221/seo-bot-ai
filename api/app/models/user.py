"""
Modelo de Usuario - Tabla espejo del usuario externo (Shadow User).
Sincroniza datos desde la API externa de Herandro Services.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class User(SQLModel, table=True):
    """
    Usuario local que refleja el usuario de la API externa.
    Se crea automáticamente al verificar el token.
    """
    __tablename__ = "users"

    # ID local
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # ID del usuario en la API externa de Herandro
    external_id: UUID = Field(unique=True, index=True)

    # Información del usuario
    email: str = Field(index=True)
    full_name: str
    username: Optional[str] = None

    # Relaciones con tenant y proyecto
    tenant_id: Optional[UUID] = Field(default=None, index=True)
    project_id: Optional[UUID] = Field(default=None, index=True)

    # Metadatos de sincronización
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "Juan Perez",
                "external_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "tenant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        }

