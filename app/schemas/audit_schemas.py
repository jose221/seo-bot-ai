"""
Schemas para Auditorías.
Define DTOs para crear y consultar reportes de análisis.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.audit import AuditStatus


class AuditCreate(BaseModel):
    """Schema para iniciar una auditoría"""
    web_page_id: UUID = Field(..., description="ID del target a auditar")
    include_ai_analysis: bool = Field(
        default=True,
        description="Si incluir análisis de IA (consume más tiempo)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "web_page_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "include_ai_analysis": True
            }
        }


class AuditTaskResponse(BaseModel):
    """Respuesta inmediata al iniciar auditoría"""
    task_id: UUID
    status: AuditStatus
    message: str = "Auditoría iniciada en segundo plano"

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "pending",
                "message": "Auditoría iniciada en segundo plano"
            }
        }


class AuditResponse(BaseModel):
    """Respuesta completa de una auditoría"""
    id: UUID
    web_page_id: UUID
    user_id: UUID
    status: AuditStatus

    # Scores
    performance_score: Optional[float]
    seo_score: Optional[float]
    accessibility_score: Optional[float]
    best_practices_score: Optional[float]

    # Core Web Vitals
    lcp: Optional[float]
    fid: Optional[float]
    cls: Optional[float]

    # Datos completos
    lighthouse_data: Optional[Dict[str, Any]]
    ai_suggestions: Optional[Dict[str, Any]]

    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """Lista de auditorías con paginación"""
    items: list[AuditResponse]
    total: int
    page: int
    page_size: int

