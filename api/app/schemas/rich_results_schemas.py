"""
Schemas para generación de reportes de Google Rich Results.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.rich_results_report import RichResultsReportStatus


class RichResultsScreenshot(BaseModel):
    path: str
    url: str


class RichResultsAIResult(BaseModel):
    content: str
    usage: Optional[dict] = None
    model: Optional[str] = None
    generated_at: Optional[str] = None


class RichResultsAnalysisFinding(BaseModel):
    key: str
    code: str
    severity: str
    category: str
    selector: str
    message: str
    document_url: Optional[str] = None
    document_label: Optional[str] = None
    element_url: Optional[str] = None
    item_name: Optional[str] = None
    color: Optional[str] = None


class RichResultsAnalysisSummary(BaseModel):
    total: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)


class RichResultsValidatorDetail(BaseModel):
    validator: str
    label: str
    enabled: bool = False
    executed: bool = False
    success: Optional[bool] = None
    method_used: Optional[str] = None
    result_url: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    blocked: bool = False
    screenshots: List[RichResultsScreenshot] = Field(default_factory=list)
    findings: List[RichResultsAnalysisFinding] = Field(default_factory=list)
    findings_summary: RichResultsAnalysisSummary = Field(default_factory=RichResultsAnalysisSummary)
    html_content: Optional[str] = None
    markdown_content: Optional[str] = None


class RichResultsReportRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        description="Contenido a validar. Puede ser una URL o un HTML completo, según el valor de is_url."
    )
    is_url: bool = Field(
        ...,
        description="Si es true, content se interpreta como URL. Si es false, content se interpreta como HTML."
    )
    get_ai_result: bool = Field(
        default=False,
        description="Si es true, convierte el HTML final de Google a markdown y solicita análisis al agente de IA."
    )
    auto_extract_html: bool = Field(
        default=False,
        description="Si es true y content es una URL, primero extrae el HTML con el scraper propio y valida ese HTML en lugar de enviar la URL directo a Google.",
    )
    validate_google: bool = Field(
        default=True,
        description="Si es true ejecuta la validación en Google Rich Results.",
    )
    validate_schema_org: bool = Field(
        default=True,
        description="Si es true ejecuta la validación en validator.schema.org.",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content no puede estar vacío")
        return value

    @model_validator(mode="after")
    def validate_single_input(self) -> "RichResultsReportRequest":
        if self.is_url and not self.content.startswith(("http://", "https://")):
            raise ValueError("Cuando is_url es true, content debe comenzar con http:// o https://")

        if not self.is_url and "<" not in self.content:
            raise ValueError("Cuando is_url es false, content debe parecer HTML válido")
        if self.auto_extract_html and not self.is_url:
            raise ValueError("auto_extract_html solo se puede usar cuando is_url es true")
        if not self.validate_google and not self.validate_schema_org:
            raise ValueError("Se debe activar al menos uno entre validate_google y validate_schema_org")
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "content": "https://example.com/producto",
                    "is_url": True,
                    "get_ai_result": True,
                    "auto_extract_html": False,
                    "validate_google": True,
                    "validate_schema_org": True,
                },
                {
                    "content": "<html><body><script type='application/ld+json'>{}</script></body></html>",
                    "is_url": False,
                    "get_ai_result": False,
                    "auto_extract_html": False,
                    "validate_google": True,
                    "validate_schema_org": True,
                }
            ]
        }


class RichResultsBatchReportRequest(BaseModel):
    urls: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de URLs para generar reportes Rich Results en lote.",
    )
    get_ai_result: bool = Field(
        default=True,
        description="Si es true, solicita también el análisis de IA para cada URL.",
    )
    auto_extract_html: bool = Field(
        default=False,
        description="Si es true, cada URL del lote primero se convierte a HTML con el scraper propio y ese HTML se usa para la validación Rich Results.",
    )
    validate_google: bool = Field(
        default=True,
        description="Si es true ejecuta la validación en Google Rich Results para cada URL del lote.",
    )
    validate_schema_org: bool = Field(
        default=True,
        description="Si es true ejecuta la validación en validator.schema.org para cada URL del lote.",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, value: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()

        for raw_url in value:
            url = (raw_url or "").strip()
            if not url:
                continue
            if not url.startswith(("http://", "https://")):
                raise ValueError("Todas las URLs deben comenzar con http:// o https://")
            if url in seen:
                continue
            seen.add(url)
            normalized.append(url)

        if not normalized:
            raise ValueError("Se requiere al menos una URL válida")

        return normalized

    @model_validator(mode="after")
    def validate_requested_validators(self) -> "RichResultsBatchReportRequest":
        if not self.validate_google and not self.validate_schema_org:
            raise ValueError("Se debe activar al menos uno entre validate_google y validate_schema_org")
        return self


class RichResultsReportResponse(BaseModel):
    success: bool
    input_type: str
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
    validate_google: bool = True
    validate_schema_org: bool = True
    screenshots: List[RichResultsScreenshot] = Field(default_factory=list)
    findings: List[RichResultsAnalysisFinding] = Field(default_factory=list)
    findings_summary: RichResultsAnalysisSummary = Field(default_factory=RichResultsAnalysisSummary)
    google_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="google", label="Google Rich Results")
    )
    schema_org_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="schema_org", label="Schema.org Validator")
    )
    get_ai_result: Optional[RichResultsAIResult] = None
    ai_error_message: Optional[str] = None
    report_id: Optional[UUID] = None
    saved: bool = False


class RichResultsReportTaskResponse(BaseModel):
    task_id: UUID
    status: RichResultsReportStatus
    progress_percentage: int = 0
    progress_message: Optional[str] = None
    url: str
    message: str = "Reporte de Google Rich Results iniciado en segundo plano"


class RichResultsBatchReportResponse(BaseModel):
    total: int
    created_count: int
    items: List[RichResultsReportTaskResponse]
    message: str


class RichResultsReportListItem(BaseModel):
    id: UUID
    url: str
    status: RichResultsReportStatus
    progress_percentage: int = 0
    progress_message: Optional[str] = None
    input_type: str
    requested_ai_result: bool = False
    validate_google: bool = True
    validate_schema_org: bool = True
    success: bool
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
    findings_summary: RichResultsAnalysisSummary = Field(default_factory=RichResultsAnalysisSummary)
    google_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="google", label="Google Rich Results")
    )
    schema_org_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="schema_org", label="Schema.org Validator")
    )
    created_at: datetime


class RichResultsReportListResponse(BaseModel):
    items: List[RichResultsReportListItem]
    total: int
    page: int
    page_size: Optional[int] = None


class RichResultsReportDetailResponse(BaseModel):
    id: UUID
    url: str
    status: RichResultsReportStatus
    progress_percentage: int = 0
    progress_message: Optional[str] = None
    input_type: str
    requested_ai_result: bool = False
    validate_google: bool = True
    validate_schema_org: bool = True
    success: bool
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
    screenshots: List[RichResultsScreenshot] = Field(default_factory=list)
    findings: List[RichResultsAnalysisFinding] = Field(default_factory=list)
    findings_summary: RichResultsAnalysisSummary = Field(default_factory=RichResultsAnalysisSummary)
    google_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="google", label="Google Rich Results")
    )
    schema_org_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="schema_org", label="Schema.org Validator")
    )
    get_ai_result: Optional[RichResultsAIResult] = None
    ai_error_message: Optional[str] = None
    created_at: datetime


class DeleteRichResultsReportResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int
    report_id: Optional[UUID] = None
    url: Optional[str] = None


class RichResultsReportStatusSummaryItem(BaseModel):
    url: str
    state: str
    report_id: Optional[UUID] = None
    report_status: Optional[RichResultsReportStatus] = None
    progress_percentage: int = 0
    progress_message: Optional[str] = None
    success: Optional[bool] = None
    blocked_by_google: Optional[bool] = None
    validate_google: bool = True
    validate_schema_org: bool = True
    has_error: bool = False
    message: Optional[str] = None
    error_message: Optional[str] = None
    findings_summary: RichResultsAnalysisSummary = Field(default_factory=RichResultsAnalysisSummary)
    google_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="google", label="Google Rich Results")
    )
    schema_org_validation: RichResultsValidatorDetail = Field(
        default_factory=lambda: RichResultsValidatorDetail(validator="schema_org", label="Schema.org Validator")
    )
    created_at: Optional[datetime] = None


class RichResultsReportStatusSummaryResponse(BaseModel):
    items: List[RichResultsReportStatusSummaryItem]
