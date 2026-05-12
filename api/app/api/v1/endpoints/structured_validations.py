from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.structured_validation_comment import StructuredValidationComment
from app.models.structured_validation_task import StructuredValidationTask, StructuredValidationTaskStatus
from app.models.url_validation_comment import CommentStatus
from app.models.user import User
from app.schemas.rich_results_schemas import RichResultsReportRequest
from app.schemas.audit_schemas import CommentListResponse, CommentResponse
from app.schemas.structured_validation_schemas import (
    StructuredValidationBrowserModeOption,
    StructuredValidationTaskAction,
    StructuredValidationTaskActionRequest,
    StructuredValidationCommentAnswerRequest,
    StructuredValidationCreateRequest,
    StructuredValidationDeleteResponse,
    StructuredValidationPublicCommentCreate,
    StructuredValidationRerunResponse,
    StructuredValidationTaskCreateResponse,
    StructuredValidationTaskListResponse,
    StructuredValidationTaskResponse,
)
from app.services.rich_results_report_service import get_rich_results_report_service
from app.services.task_notification_service import get_task_notification_service
from app.services.structured_validation_task_service import get_structured_validation_task_service
from app.services.task_progress_service import get_task_progress_service
from app.schemas.task_log_schemas import TaskLogEntryResponse, TaskLogListResponse

router = APIRouter(prefix="/structured-validations")


@router.get("/browser-modes", response_model=list[StructuredValidationBrowserModeOption])
async def list_structured_validation_browser_modes():
    return get_structured_validation_task_service().list_available_browser_modes()


@router.post("", response_model=StructuredValidationTaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_structured_validation_task(
    payload: StructuredValidationCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        task = await get_structured_validation_task_service().create_task(
            session,
            user_id=current_user.id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    background_tasks.add_task(
        get_structured_validation_task_service().run_task,
        task_id=task.id,
        token=getattr(current_user, "_token", None) or "",
    )
    return StructuredValidationTaskCreateResponse(
        task_id=task.id,
        status=task.status,
        progress_percentage=task.progress_percentage,
        progress_message=task.progress_message,
        total_items=task.total_items,
        message="Tarea de validacion estructurada encolada",
    )


@router.get("", response_model=StructuredValidationTaskListResponse)
async def list_structured_validation_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    return await get_structured_validation_task_service().list_tasks(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=StructuredValidationTaskResponse)
async def get_structured_validation_task(
    task_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=10000),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id, user_id=current_user.id)
    if task:
        return get_structured_validation_task_service().build_task_response(task, page=page, page_size=page_size)
    report = await get_structured_validation_task_service().get_legacy_report(
        session,
        task_id=task_id,
        user_id=current_user.id,
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return get_structured_validation_task_service().build_legacy_response(report, page=page, page_size=page_size)


@router.get("/{task_id}/logs", response_model=TaskLogListResponse)
async def get_structured_validation_task_logs(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id, user_id=current_user.id)
    if task:
        items = await get_task_progress_service().list_logs(
            session,
            task_type="structured_validation_task",
            task_id=task_id,
        )
        return TaskLogListResponse(
            task_type="structured_validation_task",
            task_id=task_id,
            items=[TaskLogEntryResponse.model_validate(item) for item in reversed(items)],
        )

    report = await get_structured_validation_task_service().get_legacy_report(
        session,
        task_id=task_id,
        user_id=current_user.id,
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    items = await get_task_progress_service().list_logs(
        session,
        task_type="rich_results_report",
        task_id=task_id,
    )
    return TaskLogListResponse(
        task_type="rich_results_report",
        task_id=task_id,
        items=[TaskLogEntryResponse.model_validate(item) for item in reversed(items)],
    )


@router.get("/{task_id}/public", response_model=StructuredValidationTaskResponse, tags=["Público"])
async def get_structured_validation_task_public(
    task_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=10000),
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id)
    if task:
        return get_structured_validation_task_service().build_task_response(task, page=page, page_size=page_size)
    report = await get_structured_validation_task_service().get_legacy_report(session, task_id=task_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return get_structured_validation_task_service().build_legacy_response(report, page=page, page_size=page_size)


@router.post("/{task_id}/actions", response_model=StructuredValidationTaskResponse)
async def control_structured_validation_task(
    task_id: UUID,
    body: StructuredValidationTaskActionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    task_service = get_structured_validation_task_service()
    task = await task_service.get_task(session, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o no controlable")

    try:
        if body.action == StructuredValidationTaskAction.PAUSE:
            task = await task_service.pause_task(session, task=task)
        elif body.action == StructuredValidationTaskAction.RESUME:
            task = await task_service.resume_task(session, task=task)
        elif body.action == StructuredValidationTaskAction.CANCEL:
            task = await task_service.cancel_task(session, task=task)
        else:
            if task.status in {
                StructuredValidationTaskStatus.PENDING,
                StructuredValidationTaskStatus.IN_PROGRESS,
                StructuredValidationTaskStatus.PAUSED,
            }:
                raise ValueError("No puedes reiniciar una tarea activa; primero pausala o cancelala")
            task = await task_service.rerun_task(session, task=task)
            background_tasks.add_task(
                task_service.run_task,
                task_id=task.id,
                token=getattr(current_user, "_token", None) or "",
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return task_service.build_task_response(task)


@router.post("/{task_id}/rerun", response_model=StructuredValidationRerunResponse, status_code=status.HTTP_202_ACCEPTED)
async def rerun_structured_validation_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    task_service = get_structured_validation_task_service()
    task = await task_service.get_task(session, task_id=task_id, user_id=current_user.id)
    if task:
        if task.status in {
            StructuredValidationTaskStatus.PENDING,
            StructuredValidationTaskStatus.IN_PROGRESS,
            StructuredValidationTaskStatus.PAUSED,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puedes reiniciar una tarea activa; primero pausala o cancelala",
            )
        task = await task_service.rerun_task(session, task=task)
        background_tasks.add_task(
            task_service.run_task,
            task_id=task.id,
            token=getattr(current_user, "_token", None) or "",
        )
        return StructuredValidationRerunResponse(
            task_id=task.id,
            status=task.status,
            progress_percentage=task.progress_percentage,
            progress_message=task.progress_message,
            message="Reejecucion encolada",
        )

    report = await get_structured_validation_task_service().get_legacy_report(
        session,
        task_id=task_id,
        user_id=current_user.id,
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    report.status = "pending"
    report.progress_percentage = 0
    report.progress_message = "Reporte de validación estructurada en cola"
    report.success = False
    report.error_message = None
    report.ai_error_message = None
    report.message = "Reporte de validación estructurada en cola"
    session.add(report)
    await session.commit()

    background_tasks.add_task(
        get_rich_results_report_service().run_report_task,
        report_id=report.id,
        payload=RichResultsReportRequest(
            content=report.url,
            is_url=True,
            get_ai_result=report.requested_ai_result,
            auto_extract_html=False,
            validate_google=report.validate_google,
            validate_schema_org=report.validate_schema_org,
            browser_mode_code=None,
        ),
        token=getattr(current_user, "_token", None) or "",
    )
    return StructuredValidationRerunResponse(
        task_id=report.id,
        status=report.status,
        progress_percentage=report.progress_percentage,
        progress_message=report.progress_message,
        message="Reejecucion legacy encolada",
    )


@router.delete("/{task_id}", response_model=StructuredValidationDeleteResponse)
async def delete_structured_validation_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id, user_id=current_user.id)
    if task:
        comment_stmt = select(StructuredValidationComment).where(StructuredValidationComment.task_id == task.id)
        comments = (await session.execute(comment_stmt)).scalars().all()
        for comment in comments:
            await session.delete(comment)
        await get_structured_validation_task_service().delete_task(session, task=task)
        await get_task_notification_service().publish_structured_validation_task_change(
            user_id=current_user.id,
            action="deleted",
            task_id=task_id,
            route=f"/admin/audit/structured-validations/{task_id}/info",
        )
        return StructuredValidationDeleteResponse(deleted_id=task_id, message="Tarea eliminada")

    report = await get_structured_validation_task_service().get_legacy_report(
        session,
        task_id=task_id,
        user_id=current_user.id,
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    await session.delete(report)
    await session.commit()
    return StructuredValidationDeleteResponse(deleted_id=task_id, message="Reporte legacy eliminado")


@router.get("/{task_id}/comments", response_model=CommentListResponse, tags=["Público"])
async def list_structured_validation_comments(
    task_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id)
    if not task:
        report = await get_structured_validation_task_service().get_legacy_report(session, task_id=task_id)
        if report:
            return CommentListResponse(
                validation_id=task_id,
                total=0,
                page=page,
                page_size=page_size,
                items=[],
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    stmt_total = select(func.count()).select_from(StructuredValidationComment).where(
        StructuredValidationComment.task_id == task_id
    )
    total = (await session.execute(stmt_total)).scalar_one()
    stmt = (
        select(StructuredValidationComment)
        .where(StructuredValidationComment.task_id == task_id)
        .order_by(StructuredValidationComment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()
    return CommentListResponse(
        validation_id=task_id,
        total=total,
        page=page,
        page_size=page_size,
        items=[
            CommentResponse(
                id=item.id,
                validation_id=item.task_id,
                schema_item_url=item.item_key,
                username=item.username,
                comment=item.comment,
                status=item.status,
                answer=item.answer,
                answered_at=item.answered_at,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.post("/public/{item_key:path}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, tags=["Público"])
async def create_structured_validation_comment(
    item_key: str,
    task_id: UUID = Query(...),
    body: StructuredValidationPublicCommentCreate = ...,
    session=Depends(get_session),
):
    task = await get_structured_validation_task_service().get_task(session, task_id=task_id)
    if not task:
        if await get_structured_validation_task_service().get_legacy_report(session, task_id=task_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Los reportes legacy no soportan comentarios")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    if item_key not in {item.get("item_key") for item in (task.inputs_json or [])}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento no encontrado")
    comment = StructuredValidationComment(
        task_id=task_id,
        item_key=item_key,
        username=body.username,
        comment=body.comment,
        status=CommentStatus.PENDING,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return CommentResponse(
        id=comment.id,
        validation_id=comment.task_id,
        schema_item_url=comment.item_key,
        username=comment.username,
        comment=comment.comment,
        status=comment.status,
        answer=comment.answer,
        answered_at=comment.answered_at,
        created_at=comment.created_at,
    )


@router.patch("/comments/{comment_id}/answer", response_model=CommentResponse)
async def answer_structured_validation_comment(
    comment_id: UUID,
    body: StructuredValidationCommentAnswerRequest,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    stmt = select(StructuredValidationComment).where(StructuredValidationComment.id == comment_id)
    comment = (await session.execute(stmt)).scalars().first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado")

    task = await get_structured_validation_task_service().get_task(
        session,
        task_id=comment.task_id,
        user_id=current_user.id,
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para responder este comentario")

    allowed_statuses = {status.value for status in CommentStatus}
    if body.status not in allowed_statuses:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado invalido")

    comment.answer = body.answer
    comment.status = CommentStatus(body.status)
    comment.answered_at = datetime.utcnow()
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return CommentResponse(
        id=comment.id,
        validation_id=comment.task_id,
        schema_item_url=comment.item_key,
        username=comment.username,
        comment=comment.comment,
        status=comment.status,
        answer=comment.answer,
        answered_at=comment.answered_at,
        created_at=comment.created_at,
    )
