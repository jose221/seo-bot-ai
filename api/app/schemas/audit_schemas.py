"""
Schemas para Auditorías.
Define DTOs para crear y consultar reportes de análisis.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from datetime import datetime

from app.models import WebPage, ComparisonStatus, SchemaAuditStatus, SchemaAuditSourceType
from app.models.audit import AuditStatus
from app.models.audit_url_validation import UrlValidationStatus, UrlValidationSourceType


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


class WebPageSimpleResponse(BaseModel):
    """WebPage simplificada para listados: omite manual_html_content que es muy pesado."""
    id: UUID
    url: str
    name: Optional[str]
    instructions: Optional[str]
    tech_stack: Optional[str]
    tags: Optional[List[str]]
    provider: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class AuditResponse(BaseModel):
    """Respuesta completa de una auditoría individual (find). Incluye web_page completa."""
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
    web_page: Optional[WebPage] = None  # Modelo completo: incluye manual_html_content

    class Config:
        from_attributes = True


class AuditListItem(BaseModel):
    """Item de auditoría para listados. Omite manual_html_content de web_page para aligerar la respuesta."""
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
    web_page: Optional[WebPageSimpleResponse] = None  # Sin manual_html_content

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """Lista de auditorías con paginación (sin manual_html_content en web_page)"""
    items: list[AuditListItem]
    total: int
    page: int
    page_size: Optional[int] = None


class AuditListItemLite(BaseModel):
    """Item liviano para el listado de auditorías.
    Solo incluye las columnas visibles en la tabla del frontend.
    NO incluye lighthouse_data, ai_suggestions ni seo_analysis (JSONB pesados).
    """
    id: UUID
    web_page_id: UUID
    user_id: UUID
    status: AuditStatus

    # Scores visibles en la tabla
    performance_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    best_practices_score: Optional[float] = None

    # Core Web Vitals visibles en la tabla
    fid: Optional[float] = None
    cls: Optional[float] = None

    # Rutas de reportes (botones Ver / Schema / Validar URLs)
    report_pdf_path: Optional[str] = None
    report_excel_path: Optional[str] = None
    report_word_path: Optional[str] = None

    # Fechas
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Solo la url de la web_page (columna "Página Web")
    web_page_url: Optional[str] = None

    class Config:
        from_attributes = True


class AuditListLiteResponse(BaseModel):
    """Lista liviana de auditorías para la tabla principal."""
    items: list[AuditListItemLite]
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

    # Rutas de reporte detallado de propuesta de schema
    proposal_report_pdf_path: Optional[str] = None
    proposal_report_word_path: Optional[str] = None

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

    # Rutas de reporte detallado de propuesta de schema
    proposal_report_pdf_path: Optional[str] = None
    proposal_report_word_path: Optional[str] = None

    class Config:
        from_attributes = True


ALLOWED_PROGRAMMING_LANGUAGES = {
    "c#", "csharp", "typescript", "javascript", "python", "java", "go", "kotlin", "php"
}


class AuditSchemasCreate(BaseModel):
    """Request para iniciar auditoría de schemas"""
    source_type: Literal["audit_page", "audit_comparison"] = Field(
        ..., description="Origen del esquema base"
    )
    source_id: UUID = Field(..., description="ID del recurso origen")
    modified_schema_json: Any = Field(..., description="Esquema modificado enviado por cliente")
    include_ai_analysis: bool = Field(default=True)
    programming_language: Optional[str] = Field(
        default=None,
        description="Lenguaje opcional para el modelo CQRS + SOLID"
    )

    @field_validator("programming_language")
    @classmethod
    def validate_programming_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().lower()
        if normalized not in ALLOWED_PROGRAMMING_LANGUAGES:
            raise ValueError(f"Lenguaje no válido. Permitidos: {sorted(ALLOWED_PROGRAMMING_LANGUAGES)}")
        return normalized


class AuditSchemasTaskResponse(BaseModel):
    task_id: UUID
    status: SchemaAuditStatus
    message: str = "Auditoría de schemas iniciada en segundo plano"


class AuditSchemasListItem(BaseModel):
    id: UUID
    source_type: SchemaAuditSourceType
    source_id: UUID
    status: SchemaAuditStatus
    programming_language: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    report_pdf_path: Optional[str] = None
    report_word_path: Optional[str] = None


class AuditSchemasListResponse(BaseModel):
    items: List[AuditSchemasListItem]
    total: int
    page: int
    page_size: Optional[int] = None


class AuditSchemasDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    source_type: SchemaAuditSourceType
    source_id: UUID
    status: SchemaAuditStatus

    original_schema_json: Optional[Any] = None
    proposed_schema_json: Optional[Any] = None
    incoming_schema_json: Optional[Any] = None

    schema_org_validation_result: Optional[Dict[str, Any]] = None
    triple_comparison_result: Optional[Dict[str, Any]] = None
    progress_report: Optional[Dict[str, Any]] = None
    cqrs_solid_model_text: Optional[str] = None

    include_ai_analysis: bool
    programming_language: Optional[str] = None

    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    error_message: Optional[str] = None

    report_pdf_path: Optional[str] = None
    report_word_path: Optional[str] = None

    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# URL Validation Schemas
# ---------------------------------------------------------------------------

class AuditUrlValidationCreate(BaseModel):
    """Request para iniciar validación de schemas por URL"""
    urls: str = Field(
        ...,
        description="URLs separadas por salto de línea, coma o espacio"
    )
    source_type: Literal["audit_page", "audit_comparison"] = Field(
        ..., description="Origen del esquema propuesto"
    )
    source_id: UUID = Field(..., description="ID del recurso origen")
    name_validation: str = Field(
        ..., max_length=255, description="Nombre del flujo de validación"
    )
    description_validation: Optional[str] = Field(
        default=None, description="Descripción de la validación"
    )
    ai_instruction: Optional[str] = Field(
        default=None,
        description="Instrucción adicional para la IA (ej. 'Valida si tienen checkin')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "urls": "https://example.com/hotel-1\nhttps://example.com/hotel-2",
                "source_type": "audit_comparison",
                "source_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name_validation": "Validación hoteles Cancún",
                "description_validation": "Validar schemas de hoteles contra propuesta",
                "ai_instruction": "Enfócate en validar si tienen checkinTime y checkoutTime"
            }
        }


class AuditUrlValidationTaskResponse(BaseModel):
    """Respuesta inmediata al iniciar validación de URLs"""
    task_id: UUID
    status: UrlValidationStatus
    total_urls: int
    message: str = "Validación de URLs iniciada en segundo plano"


class AuditUrlValidationListItem(BaseModel):
    """Item de validación para listados"""
    id: UUID
    source_type: UrlValidationSourceType
    source_id: UUID
    name_validation: str
    description_validation: Optional[str] = None
    status: UrlValidationStatus
    global_severity: Optional[str] = None
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    error_message: Optional[str] = None
    report_pdf_path: Optional[str] = None
    report_word_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AuditUrlValidationListResponse(BaseModel):
    """Respuesta de listado de validaciones con paginación"""
    items: List[AuditUrlValidationListItem]
    total: int
    page: int
    page_size: Optional[int] = None


class AuditUrlValidationDetailResponse(BaseModel):
    """Respuesta detallada con results_json completo"""
    id: UUID
    user_id: UUID
    source_type: UrlValidationSourceType
    source_id: UUID
    name_validation: str
    description_validation: Optional[str] = None
    ai_instruction: Optional[str] = None
    status: UrlValidationStatus
    global_severity: Optional[str] = None
    results_json: Optional[Any] = None
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    error_message: Optional[str] = None
    report_pdf_path: Optional[str] = None
    report_word_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
