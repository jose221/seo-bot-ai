"""
Modelo de Auditoría de Schemas.
Permite comparar esquema original vs propuesto vs nuevo esquema.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, String
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class SchemaAuditStatus(str, Enum):
    """Estado del proceso de auditoría de schemas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SchemaAuditSourceType(str, Enum):
    """Origen del audit de schemas"""
    AUDIT_PAGE = "audit_page"
    AUDIT_COMPARISON = "audit_comparison"


class AuditSchemaReview(SQLModel, table=True):
    """
    Auditoría de schemas (original vs propuesto vs nuevo).
    """
    __tablename__ = "audit_schema_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relaciones
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Referencia al origen
    source_type: SchemaAuditSourceType = Field(
        sa_column=Column(String, nullable=False, index=True)
    )
    source_id: UUID = Field(index=True, description="ID del audit page o audit comparison")

    # Esquemas
    original_schema_json: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    proposed_schema_json: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    incoming_schema_json: Optional[Any] = Field(default=None, sa_column=Column(JSON))

    # Validaciones y resultados
    schema_org_validation_result: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    triple_comparison_result: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    progress_report: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Resultado IA (modelo completo CQRS + SOLID)
    cqrs_solid_model_text: Optional[str] = Field(default=None)

    # Parámetros
    include_ai_analysis: bool = Field(default=True)
    programming_language: Optional[str] = Field(default=None, max_length=50)

    # Estado
    status: SchemaAuditStatus = Field(
        default=SchemaAuditStatus.PENDING,
        sa_column=Column(String, nullable=False, default=SchemaAuditStatus.PENDING.value)
    )

    # Tokens
    input_tokens: Optional[int] = Field(default=0)
    output_tokens: Optional[int] = Field(default=0)

    # Reportes
    report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))

    # Metadata
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
