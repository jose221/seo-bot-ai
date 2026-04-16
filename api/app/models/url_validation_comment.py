"""
Modelo de Comentarios Públicos para items de validación de URLs.
Permite que usuarios anónimos comenten sobre los schemas de una validación pública.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, Text
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class CommentStatus(str, Enum):
    """Estado del comentario"""
    PENDING  = "pending"
    DONE     = "done"
    REJECTED = "rejected"


class UrlValidationComment(SQLModel, table=True):
    """
    Comentario público asociado a un schema item dentro de una AuditUrlValidation.
    No requiere usuario registrado; cualquiera puede comentar con un username libre.
    Solo el dueño de la validación puede responder, cambiar estado o eliminar.
    """
    __tablename__ = "url_validation_comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Referencia a la validación
    validation_id: UUID = Field(
        foreign_key="audit_url_validations.id",
        index=True,
        description="ID de la AuditUrlValidation a la que pertenece el comentario"
    )

    # URL del schema item comentado
    schema_item_url: str = Field(
        sa_column=Column(Text, nullable=False),
        description="URL del item de schema sobre el que se comenta"
    )

    # Datos públicos del comentarista
    username: str = Field(max_length=150, description="Nombre público del comentarista")
    comment: str = Field(sa_column=Column(Text, nullable=False))

    # Estado: pending → done / rejected
    status: CommentStatus = Field(
        default=CommentStatus.PENDING,
        sa_column=Column(String(20), nullable=False, default=CommentStatus.PENDING.value)
    )

    # Respuesta del dueño de la validación
    answer: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    answered_at: Optional[datetime] = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
