"""
Schemas para Auditorías.
Define DTOs para crear y consultar reportes de análisis.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.models import WebPage, ComparisonStatus
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


class AuditCompare(BaseModel):
    """Schema para iniciar una auditoría"""
    web_page_id: UUID = Field(..., description="ID del target base de la comparación")
    web_page_id_to_compare: List[UUID] = Field(..., description="ID del target a comparar")
    include_ai_analysis: bool = Field(
        default=True,
        description="Si incluir análisis de IA (consume más tiempo)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "web_page_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "web_page_id_to_compare": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
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

    # Rutas de reportes generados
    report_pdf_path: Optional[str] = None
    report_excel_path: Optional[str] = None
    report_word_path: Optional[str] = None

    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    web_page: Optional[WebPage] = None

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """Lista de auditorías con paginación"""
    items: list[AuditResponse]
    total: int
    page: int
    page_size: Optional[int] = None


class SchemaComparisonResult(BaseModel):
    """Resultado de comparación de schemas"""
    base_schemas: list[str]
    compare_schemas: list[str]
    missing_in_base: list[str]
    common_schemas: list[str]
    unique_to_base: list[str]
    base_count: int
    compare_count: int
    completeness_score: float


class PerformanceComparisonResult(BaseModel):
    """Resultado de comparación de rendimiento"""
    scores: Dict[str, Any]
    core_web_vitals: Dict[str, Any]
    overall_better: str


class SingleComparisonResult(BaseModel):
    """Resultado de una comparación individual"""
    compare_url: str
    comparison_date: Optional[str]
    summary: Dict[str, Any]
    performance: PerformanceComparisonResult
    schemas: SchemaComparisonResult
    seo_analysis: Dict[str, Any]
    recommendations: list[Dict[str, Any]]
    ai_analysis: Optional[str] = None


class AuditComparisonResponse(BaseModel):
    """Respuesta completa de comparación de auditorías con múltiples competidores"""
    base_url: str
    comparisons: list[SingleComparisonResult]
    overall_summary: Dict[str, Any] = Field(
        description="Resumen general comparando contra todos los competidores"
    )
    ai_schema_comparison: str
    raw_schemas: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "base_url": "https://example.com",
                "comparisons": [
                    {
                        "compare_url": "https://competitor1.com",
                        "summary": {
                            "overall_winner": "base"
                        },
                        "recommendations": [
                            {
                                "category": "schema_markup",
                                "priority": "high",
                                "title": "Implementar schemas faltantes"
                            }
                        ]
                    }
                ],
                "overall_summary": {
                    "best_in_performance": "base",
                    "best_in_seo": "competitor1",
                    "areas_to_improve": ["schema_markup", "core_web_vitals"]
                },
                "ai_schema_comparison": "El sitio base tiene un 80% de schemas implementados, mientras que los competidores tienen un promedio del 65%. Se recomienda añadir los siguientes schemas: Product, FAQ, HowTo."
            }
        }


class AuditSearchItem(BaseModel):
    """Item de búsqueda simplificado para audits"""
    id: UUID
    web_page_id: UUID
    status: AuditStatus
    performance_score: Optional[float]
    seo_score: Optional[float]
    accessibility_score: Optional[float]
    best_practices_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    # Información de la página web asociada
    web_page_url: Optional[str] = None
    web_page_name: Optional[str] = None
    # Rutas de reportes generados
    report_pdf_path: Optional[str] = None
    report_excel_path: Optional[str] = None
    report_word_path: Optional[str] = None

    class Config:
        from_attributes = True


class AuditSearchResponse(BaseModel):
    """Respuesta de búsqueda de audits con paginación"""
    items: List[AuditSearchItem]
    total: int
    page: int
    page_size: Optional[int] = None


class ComparisonTaskResponse(BaseModel):
    """Respuesta inmediata al iniciar comparación"""
    task_id: UUID
    status: ComparisonStatus
    message: str = "Comparación iniciada en segundo plano"

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "pending",
                "message": "Comparación iniciada en segundo plano"
            }
        }


class ComparisonListItem(BaseModel):
    """Item simplificado de comparación para listados"""
    id: UUID
    base_web_page_id: UUID
    status: ComparisonStatus
    created_at: datetime
    completed_at: Optional[datetime]
    # Datos del resultado si está completado
    base_url: Optional[str] = None
    total_competitors: Optional[int] = None
    error_message: Optional[str] = None
    # Rutas de reportes generados
    report_pdf_path: Optional[str] = None
    report_excel_path: Optional[str] = None
    report_word_path: Optional[str] = None

    class Config:
        from_attributes = True


class ComparisonListResponse(BaseModel):
    """Respuesta de listado de comparaciones con paginación"""
    items: List[ComparisonListItem]
    total: int
    page: int
    page_size: Optional[int] = None


class ComparisonDetailResponse(BaseModel):
    """Respuesta detallada de una comparación específica"""
    id: UUID
    base_web_page_id: UUID
    status: ComparisonStatus
    created_at: datetime
    completed_at: Optional[datetime]
    comparison_result: Optional[AuditComparisonResponse] = None
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    error_message: Optional[str] = None
    # Rutas de reportes generados
    report_pdf_path: Optional[str] = None
    report_excel_path: Optional[str] = None
    report_word_path: Optional[str] = None

    class Config:
        from_attributes = True

