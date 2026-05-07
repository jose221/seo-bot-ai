"""
Modelo genérico para persistir mensajes de progreso y logs de tareas.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text
from sqlmodel import Column, Field, SQLModel


class TaskExecutionLog(SQLModel, table=True):
    __tablename__ = "task_execution_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_type: str = Field(sa_column=Column(String(80), nullable=False, index=True))
    task_id: UUID = Field(index=True)
    level: str = Field(default="info", sa_column=Column(String(20), nullable=False, default="info"))
    message: str = Field(sa_column=Column(Text, nullable=False))
    progress_percentage: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
