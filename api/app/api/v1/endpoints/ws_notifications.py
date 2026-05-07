"""
Endpoints WebSocket para notificaciones de tareas.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.api.deps import get_user_from_token
from app.core.database import db_manager
from app.services.task_notification_service import get_task_notification_service

router = APIRouter(prefix="/ws")


@router.websocket("/task-notifications")
async def task_notifications_websocket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    try:
        async with db_manager.async_session_context() as session:
            user = await get_user_from_token(session=session, token=token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    notification_service = get_task_notification_service()
    await notification_service.connect(user_id=user.id, websocket=websocket)

    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        await notification_service.disconnect(user_id=user.id, websocket=websocket)
