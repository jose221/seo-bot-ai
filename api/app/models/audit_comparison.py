"""
Modelo de Comparación de Auditorías.
Almacena resultados de comparaciones entre auditorías.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, String
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class ComparisonStatus(str, Enum):
    """Estado del proceso de comparación"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditComparison(SQLModel, table=True):
    """
    Comparación de auditorías.
    Contiene resultados de comparación entre página base y competidores.
    """
    __tablename__ = "audit_comparisons"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relaciones
    base_web_page_id: UUID = Field(foreign_key="web_pages.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # IDs de las páginas comparadas
    competitor_web_page_ids: list[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="IDs de las páginas competidoras"
    )

    # Estado
    status: ComparisonStatus = Field(
        default=ComparisonStatus.PENDING,
        sa_column=Column(String, nullable=False, default=ComparisonStatus.PENDING.value)
    )

    # Resultado de la comparación (JSONB)
    comparison_result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Resultado completo de la comparación"
    )

    # Rutas de reportes generados
    report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_excel_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))

    # Rutas de reporte detallado de propuesta de schema
    proposal_report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    proposal_report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))

    # Metadata
    include_ai_analysis: bool = Field(default=True)
    input_tokens: Optional[int] = Field(default=0, description="Tokens de entrada usados por la IA")
    output_tokens: Optional[int] = Field(default=0, description="Tokens de salida generados por la IA")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "base_web_page_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "competitor_web_page_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
            }
        }
