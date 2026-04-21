"""
Modelo de Usuario — Shadow User sincronizado desde Keycloak JWT.
Se crea automáticamente al validar el token la primera vez.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class User(SQLModel, table=True):
    """
    Usuario local que refleja al usuario autenticado por Keycloak.
    Se crea automáticamente en la primera request autenticada.
    """
    __tablename__ = "users"

    # ID local
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # sub del JWT de Keycloak (puede ser None si no se obtuvo como UUID válido)
    external_id: Optional[UUID] = Field(default=None, unique=True, index=True)

    # Datos básicos extraídos del JWT (claims estándar de OIDC)
    email: str = Field(unique=True, index=True)
    full_name: str
    username: Optional[str] = Field(default=None, index=True)

    # Metadatos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "Juan Perez",
                "external_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        }


