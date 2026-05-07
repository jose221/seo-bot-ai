"""
Servicio para persistir logs y mensajes de progreso de tareas.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlmodel import desc, select

from app.core.database import db_manager
from app.models.task_execution_log import TaskExecutionLog


class TaskProgressService:
    def log_sync(
        self,
        *,
        task_type: str,
        task_id: UUID,
        message: str,
        level: str = "info",
        progress_percentage: int | None = None,
    ) -> None:
        with db_manager.sync_session_context() as session:
            session.add(
                TaskExecutionLog(
                    task_type=task_type,
                    task_id=task_id,
                    level=level,
                    message=message,
                    progress_percentage=progress_percentage,
                )
            )

    async def list_logs(
        self,
        session,
        *,
        task_type: str,
        task_id: UUID,
        limit: Optional[int] = 200,
    ) -> list[TaskExecutionLog]:
        statement = (
            select(TaskExecutionLog)
            .where(
                TaskExecutionLog.task_type == task_type,
                TaskExecutionLog.task_id == task_id,
            )
            .order_by(desc(TaskExecutionLog.created_at))
        )
        if limit is not None:
            statement = statement.limit(limit)
        return (await session.execute(statement)).scalars().all()


_task_progress_service: TaskProgressService | None = None


def get_task_progress_service() -> TaskProgressService:
    global _task_progress_service
    if _task_progress_service is None:
        _task_progress_service = TaskProgressService()
    return _task_progress_service
