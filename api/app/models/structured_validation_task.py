from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text, Integer
from sqlmodel import Column, Field, SQLModel


class StructuredValidationInputMode(str, Enum):
    URL = "url"
    HTML = "html"


class StructuredValidationTaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StructuredValidationTask(SQLModel, table=True):
    __tablename__ = "structured_validation_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    input_mode: StructuredValidationInputMode = Field(
        sa_column=Column(String, nullable=False, index=True),
    )
    name: str = Field(default="Validacion estructurada", sa_column=Column(String(160), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    ai_instruction: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    requested_ai_result: bool = Field(default=True)
    auto_extract_html: bool = Field(default=False)
    validate_google: bool = Field(default=True)
    validate_schema_org: bool = Field(default=True)

    status: StructuredValidationTaskStatus = Field(
        default=StructuredValidationTaskStatus.PENDING,
        sa_column=Column(String, nullable=False, default=StructuredValidationTaskStatus.PENDING.value, index=True),
    )
    progress_percentage: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    progress_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    total_items: int = Field(default=0)
    completed_items: int = Field(default=0)
    successful_items: int = Field(default=0)
    failed_items: int = Field(default=0)

    inputs_json: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    results_json: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))

    success: bool = Field(default=False)
    message: str = Field(default="Tarea en cola", sa_column=Column(Text, nullable=False))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
