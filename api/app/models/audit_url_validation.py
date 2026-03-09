"""
Modelo de Validación de Schemas por URL.
Almacena los resultados de validación batch de N URLs contra un source.
"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, String
from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class UrlValidationStatus(str, Enum):
    """Estado del proceso de validación de URLs"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class UrlValidationSeverity(str, Enum):
    """Severidad global (peor caso entre todas las URLs)"""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


class UrlValidationSourceType(str, Enum):
    """Origen del esquema propuesto"""
    AUDIT_PAGE = "audit_page"
    AUDIT_COMPARISON = "audit_comparison"


class AuditUrlValidation(SQLModel, table=True):
    """
    Validación batch de schemas por URL.
    Cada registro contiene la validación de N URLs contra un source.
    """
    __tablename__ = "audit_url_validations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relaciones
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Referencia al origen
    source_type: UrlValidationSourceType = Field(
        sa_column=Column(String, nullable=False, index=True)
    )
    source_id: UUID = Field(index=True, description="ID del audit page o audit comparison")

    # Parámetros de la validación
    name_validation: str = Field(max_length=255, description="Nombre del flujo de validación")
    description_validation: Optional[str] = Field(
        default=None, description="Descripción de la validación"
    )
    ai_instruction: Optional[str] = Field(
        default=None, description="Instrucción adicional para la IA"
    )

    # URLs originales (raw string como fue enviado)
    urls_raw: Optional[str] = Field(default=None, description="URLs en formato original")

    # Estado
    status: UrlValidationStatus = Field(
        default=UrlValidationStatus.PENDING,
        sa_column=Column(String, nullable=False, default=UrlValidationStatus.PENDING.value)
    )

    # Severidad global (peor caso entre todas las URLs)
    global_severity: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="ok/warning/critical — peor caso entre todas las URLs"
    )

    # Resultado completo como JSON
    results_json: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Lista de resultados por URL"
    )

    # Reportes individuales
    report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))

    # Reporte global (resumen consolidado de todas las URLs)
    global_report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    global_report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    global_report_ai_text: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Texto/respuesta de la IA del reporte global consolidado"
    )

    # Tokens
    input_tokens: Optional[int] = Field(default=0)
    output_tokens: Optional[int] = Field(default=0)

    # Metadata
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

