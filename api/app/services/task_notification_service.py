"""
Servicio de notificaciones en tiempo real para cambios de estado de tareas.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket


@dataclass
class TaskStatusNotification:
    event: str
    task_kind: str
    task_id: str
    status: str
    route: str
    label: str
    occurred_at: str


class TaskNotificationService:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, *, user_id: UUID | str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(str(user_id), set()).add(websocket)

    async def disconnect(self, *, user_id: UUID | str, websocket: WebSocket) -> None:
        async with self._lock:
            user_connections = self._connections.get(str(user_id))
            if not user_connections:
                return
            user_connections.discard(websocket)
            if not user_connections:
                self._connections.pop(str(user_id), None)

    async def send_to_user(self, *, user_id: UUID | str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(str(user_id), set()))

        stale_sockets: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_sockets.append(websocket)

        for websocket in stale_sockets:
            await self.disconnect(user_id=user_id, websocket=websocket)

    async def publish_task_status_change(
        self,
        *,
        user_id: UUID | str,
        task_kind: str,
        task_id: UUID | str,
        status: str,
        route: str,
        label: str,
    ) -> None:
        payload = TaskStatusNotification(
            event="task-status-changed",
            task_kind=task_kind,
            task_id=str(task_id),
            status=status,
            route=route,
            label=label,
            occurred_at=datetime.now(timezone.utc).isoformat(),
        )
        await self.send_to_user(user_id=user_id, payload=asdict(payload))


_task_notification_service: TaskNotificationService | None = None


def get_task_notification_service() -> TaskNotificationService:
    global _task_notification_service
    if _task_notification_service is None:
        _task_notification_service = TaskNotificationService()
    return _task_notification_service
