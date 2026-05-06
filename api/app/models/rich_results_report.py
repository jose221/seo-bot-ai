"""
Modelo para persistir reportes de Google Rich Results.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text
from sqlmodel import Column, Field, SQLModel


class RichResultsReport(SQLModel, table=True):
    """
    Reporte persistido de una ejecución de Google Rich Results para una URL.
    """

    __tablename__ = "rich_results_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    url: str = Field(index=True, description="URL origen del reporte")
    input_type: str = Field(sa_column=Column(String, nullable=False))
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

    ai_result_content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    ai_result_usage: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    ai_result_model: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    ai_generated_at: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    ai_error_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

