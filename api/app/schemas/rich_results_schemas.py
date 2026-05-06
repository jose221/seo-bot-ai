"""
Schemas para generación de reportes de Google Rich Results.
"""
from datetime import datetime
from typing import List, Optional
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
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "content": "https://example.com/producto",
                    "is_url": True,
                    "get_ai_result": True
                },
                {
                    "content": "<html><body><script type='application/ld+json'>{}</script></body></html>",
                    "is_url": False,
                    "get_ai_result": False
                }
            ]
        }


class RichResultsReportResponse(BaseModel):
    success: bool
    input_type: str
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
    screenshots: List[RichResultsScreenshot] = Field(default_factory=list)
    get_ai_result: Optional[RichResultsAIResult] = None
    ai_error_message: Optional[str] = None
    report_id: Optional[UUID] = None
    saved: bool = False


class RichResultsReportTaskResponse(BaseModel):
    task_id: UUID
    status: RichResultsReportStatus
    url: str
    message: str = "Reporte de Google Rich Results iniciado en segundo plano"


class RichResultsReportListItem(BaseModel):
    id: UUID
    url: str
    status: RichResultsReportStatus
    input_type: str
    requested_ai_result: bool = False
    success: bool
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
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
    input_type: str
    requested_ai_result: bool = False
    success: bool
    method_used: str
    result_url: Optional[str] = None
    message: str
    error_message: Optional[str] = None
    blocked_by_google: bool = False
    screenshots: List[RichResultsScreenshot] = Field(default_factory=list)
    get_ai_result: Optional[RichResultsAIResult] = None
    ai_error_message: Optional[str] = None
    created_at: datetime


class DeleteRichResultsReportResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int
    report_id: Optional[UUID] = None
    url: Optional[str] = None
