"""
Modelo para persistir reportes de Google Rich Results.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text, Integer
from sqlmodel import Column, Field, SQLModel
from enum import Enum


class RichResultsReportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RichResultsReport(SQLModel, table=True):
    """
    Reporte persistido de una ejecución de Google Rich Results para una URL.
    """

    __tablename__ = "rich_results_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    url: str = Field(index=True, description="URL origen del reporte")
    status: RichResultsReportStatus = Field(
        default=RichResultsReportStatus.PENDING,
        sa_column=Column(String, nullable=False, default=RichResultsReportStatus.PENDING.value, index=True),
    )
    progress_percentage: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, default=0),
        description="Porcentaje de avance del reporte Rich Results (0-100)",
    )
    progress_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    input_type: str = Field(sa_column=Column(String, nullable=False))
    requested_ai_result: bool = Field(default=False)
    success: bool = Field(default=False)
    method_used: str = Field(sa_column=Column(String, nullable=False))
    result_url: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    message: str = Field(sa_column=Column(Text, nullable=False))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    blocked_by_google: bool = Field(default=False)

    screenshots: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Screenshots generados durante la validación",
    )
    analysis_findings: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Hallazgos estructurados extraídos del HTML final de Google Rich Results",
    )

    ai_result_content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    ai_result_usage: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    ai_result_model: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    ai_generated_at: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    ai_error_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
