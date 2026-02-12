"""
Modelo de Reporte de Auditoría.
Almacena resultados de análisis Lighthouse + IA.
"""
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, String
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class AuditStatus(str, Enum):
    """Estado del proceso de auditoría"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditReport(SQLModel, table=True):
    """
    Reporte de auditoría SEO/Performance.
    Contiene datos estructurados de Lighthouse y análisis de IA.
    """
    __tablename__ = "audit_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relaciones
    web_page_id: UUID = Field(foreign_key="web_pages.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Estado (guardado como string en la BD)
    status: AuditStatus = Field(
        default=AuditStatus.PENDING,
        sa_column=Column(String, nullable=False, default=AuditStatus.PENDING.value)
    )

    # Datos de Lighthouse (JSONB)
    lighthouse_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Métricas completas de Lighthouse"
    )

    seo_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Seo analyzer data"
    )

    # Análisis de IA (JSONB)
    ai_suggestions: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Sugerencias y análisis generados por IA"
    )

    # Métricas clave (para búsquedas rápidas)
    performance_score: Optional[float] = Field(default=None, ge=0, le=100)
    seo_score: Optional[float] = Field(default=None, ge=0, le=100)
    accessibility_score: Optional[float] = Field(default=None, ge=0, le=100)
    best_practices_score: Optional[float] = Field(default=None, ge=0, le=100)

    # Core Web Vitals
    lcp: Optional[float] = Field(default=None, description="Largest Contentful Paint (ms)")
    fid: Optional[float] = Field(default=None, description="First Input Delay (ms)")
    cls: Optional[float] = Field(default=None, description="Cumulative Layout Shift")

    # Rutas de reportes generados
    report_pdf_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_excel_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    report_word_path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))

    # Metadata
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    web_page: Optional["WebPage"] = Relationship(back_populates="audit_reports")
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "performance_score": 85.5,
                "seo_score": 92.0,
                "lcp": 2400,
                "ai_suggestions": {
                    "summary": "El sitio tiene buen SEO pero necesita mejorar rendimiento",
                    "actions": ["Optimizar imágenes", "Reducir JavaScript"]
                },
                "web_page": {}
            }
        }
