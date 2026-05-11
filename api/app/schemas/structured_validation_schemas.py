from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.structured_validation_task import (
    StructuredValidationInputMode,
    StructuredValidationTaskStatus,
)
from app.schemas.audit_schemas import CommentAnswerUpdate, CommentCreate, CommentListResponse, CommentResponse
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportResponse,
    RichResultsValidatorDetail,
)


class StructuredValidationCreateRequest(BaseModel):
    input_mode: StructuredValidationInputMode
    name: str = Field(default="Validacion estructurada", max_length=160)
    description: Optional[str] = Field(default=None, max_length=500)
    ai_instruction: Optional[str] = Field(default=None, max_length=1200)
    raw_urls: Optional[str] = None
    html_items: List[str] = Field(default_factory=list)
    get_ai_result: bool = True
    auto_extract_html: bool = False
    validate_google: bool = True
    validate_schema_org: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = (value or "").strip()
        return cleaned or "Validacion estructurada"

    @field_validator("description", "ai_instruction")
    @classmethod
    def trim_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_payload(self) -> "StructuredValidationCreateRequest":
        if not self.validate_google and not self.validate_schema_org:
            raise ValueError("Se debe activar al menos uno entre validate_google y validate_schema_org")
        if self.input_mode == StructuredValidationInputMode.URL and self.auto_extract_html is False:
            pass
        if self.input_mode == StructuredValidationInputMode.URL:
            if not (self.raw_urls or "").strip():
                raise ValueError("Debes capturar al menos una URL")
        else:
            cleaned = [item.strip() for item in self.html_items if item and item.strip()]
            if not cleaned:
                raise ValueError("Debes capturar al menos un HTML")
            if any("<" not in item for item in cleaned):
                raise ValueError("Cada bloque HTML debe parecer contenido HTML valido")
            self.html_items = cleaned
            self.raw_urls = None
            self.auto_extract_html = False
        return self


class StructuredValidationRerunResponse(BaseModel):
    task_id: UUID
    status: StructuredValidationTaskStatus
    progress_percentage: int
    progress_message: Optional[str] = None
    message: str


class StructuredValidationTaskAction(str, Enum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RESTART = "restart"


class StructuredValidationTaskActionRequest(BaseModel):
    action: StructuredValidationTaskAction


class StructuredValidationTaskItem(BaseModel):
    item_key: str
    input_type: StructuredValidationInputMode
    label: str
    source_preview: Optional[str] = None
    source_value: Optional[str] = None
    success: bool = False
    severity: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    report: RichResultsReportResponse


class StructuredValidationTaskResponse(BaseModel):
    id: UUID
    task_kind: str = "structured_validation_task"
    supports_runtime_control: bool = True
    input_mode: StructuredValidationInputMode
    name: str
    description: Optional[str] = None
    ai_instruction: Optional[str] = None
    requested_ai_result: bool
    auto_extract_html: bool
    validate_google: bool
    validate_schema_org: bool
    status: StructuredValidationTaskStatus
    progress_percentage: int
    progress_message: Optional[str] = None
    total_items: int
    completed_items: int
    successful_items: int
    failed_items: int
    success: bool
    message: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    items: List[StructuredValidationTaskItem] = Field(default_factory=list)


class StructuredValidationTaskListItem(BaseModel):
    id: UUID
    task_kind: str = "structured_validation_task"
    supports_runtime_control: bool = True
    input_mode: StructuredValidationInputMode
    name: str
    description: Optional[str] = None
    status: StructuredValidationTaskStatus
    progress_percentage: int
    progress_message: Optional[str] = None
    total_items: int
    completed_items: int
    successful_items: int
    failed_items: int
    validate_google: bool
    validate_schema_org: bool
    requested_ai_result: bool
    created_at: datetime
    completed_at: Optional[datetime] = None


class StructuredValidationTaskListResponse(BaseModel):
    items: List[StructuredValidationTaskListItem]
    total: int
    page: int
    page_size: int


class StructuredValidationTaskCreateResponse(BaseModel):
    task_id: UUID
    status: StructuredValidationTaskStatus
    progress_percentage: int
    progress_message: Optional[str] = None
    total_items: int
    message: str


class StructuredValidationDeleteResponse(BaseModel):
    success: bool = True
    deleted_id: UUID
    message: str


StructuredValidationPublicCommentCreate = CommentCreate
StructuredValidationPublicCommentResponse = CommentResponse
StructuredValidationPublicCommentListResponse = CommentListResponse
StructuredValidationCommentAnswerRequest = CommentAnswerUpdate
