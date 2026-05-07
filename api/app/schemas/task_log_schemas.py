"""
Schemas para logs de ejecución de tareas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TaskLogEntryResponse(BaseModel):
    id: UUID
    level: str
    message: str
    progress_percentage: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskLogListResponse(BaseModel):
    task_type: str
    task_id: UUID
    items: List[TaskLogEntryResponse]
