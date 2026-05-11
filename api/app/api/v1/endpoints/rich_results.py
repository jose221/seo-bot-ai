"""
Endpoints para generación de reportes de Google Rich Results.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from uuid import UUID

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_session
from app.models.user import User
from app.schemas.rich_results_schemas import (
    DeleteRichResultsReportResponse,
    RichResultsBatchReportRequest,
    RichResultsBatchReportResponse,
    RichResultsReportDetailResponse,
    RichResultsReportListResponse,
    RichResultsReportRequest,
    RichResultsReportStatusSummaryResponse,
    RichResultsReportTaskResponse,
)
from app.schemas.task_log_schemas import TaskLogEntryResponse, TaskLogListResponse
from app.services.rich_results_report_service import get_rich_results_report_service
from app.services.task_progress_service import get_task_progress_service

router = APIRouter(prefix="/rich-results")


@router.post(
    "/report-page",
    response_model=RichResultsReportTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def report_page(
    payload: RichResultsReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    if not payload.is_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se soportan reportes basados en URL",
        )

    try:
        report = await get_rich_results_report_service().create_pending_report(
            session,
            user_id=current_user.id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    auth_token = getattr(current_user, "_token", None)
    background_tasks.add_task(
        get_rich_results_report_service().run_report_task,
        report_id=report.id,
        payload=payload,
        token=auth_token or "",
    )

    return RichResultsReportTaskResponse(
        task_id=report.id,
        status=report.status,
        progress_percentage=report.progress_percentage,
        progress_message=report.progress_message,
        url=report.url,
        message="Reporte de validación estructurada encolado",
    )


@router.post(
    "/report-page/batch",
    response_model=RichResultsBatchReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def report_page_batch(
    payload: RichResultsBatchReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    auth_token = getattr(current_user, "_token", None)
    items: list[RichResultsReportTaskResponse] = []
    queued_reports: list[tuple[UUID, RichResultsReportRequest]] = []

    for url in payload.urls:
        report_payload = RichResultsReportRequest(
            content=url,
            is_url=True,
            get_ai_result=payload.get_ai_result,
            auto_extract_html=payload.auto_extract_html,
            validate_google=payload.validate_google,
            validate_schema_org=payload.validate_schema_org,
            browser_mode_code=payload.browser_mode_code,
        )
        try:
            report = await get_rich_results_report_service().create_pending_report(
                session,
                user_id=current_user.id,
                payload=report_payload,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        queued_reports.append((report.id, report_payload))
        items.append(
            RichResultsReportTaskResponse(
                task_id=report.id,
                status=report.status,
                progress_percentage=report.progress_percentage,
                progress_message=report.progress_message,
                url=report.url,
                message="Reporte de validación estructurada encolado",
            )
        )

    if queued_reports:
        background_tasks.add_task(
            get_rich_results_report_service().run_batch_report_tasks,
            reports=queued_reports,
            token=auth_token or "",
        )

    return RichResultsBatchReportResponse(
        total=len(payload.urls),
        created_count=len(items),
        items=items,
        message="Reportes de validación estructurada encolados",
    )


@router.post("/get_reports/statuses", response_model=RichResultsReportStatusSummaryResponse)
async def get_report_statuses(
    payload: RichResultsBatchReportRequest,
    current_user: User | None = Depends(get_current_user_optional),
    session=Depends(get_session),
):
    del current_user
    return await get_rich_results_report_service().get_status_summaries(
        session,
        urls=payload.urls,
    )


@router.get("/get_reports", response_model=RichResultsReportListResponse)
async def get_reports(
    url: str | None = Query(None, description="URL exacta del reporte"),
    distinct: bool = Query(
        False,
        description="Si es true, devuelve solo el reporte más reciente por URL",
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int | None = Query(None, ge=1, le=100, description="Elementos por página"),
    current_user: User | None = Depends(get_current_user_optional),
    session=Depends(get_session),
):
    del current_user
    if not url or not url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La consulta pública de reportes requiere una URL exacta",
        )
    return await get_rich_results_report_service().list_reports(
        session,
        url=url,
        distinct=distinct,
        page=page,
        page_size=page_size,
    )


@router.get("/get_reports/{report_id}", response_model=RichResultsReportDetailResponse)
async def get_report_by_id(
    report_id: UUID,
    url: str = Query(..., min_length=1, description="URL exacta del reporte"),
    current_user: User | None = Depends(get_current_user_optional),
    session=Depends(get_session),
):
    del current_user
    report = await get_rich_results_report_service().get_report(
        session,
        report_id=report_id,
        url=url,
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    return get_rich_results_report_service().build_report_detail(report)


@router.get("/reports/{report_id}/logs", response_model=TaskLogListResponse)
async def get_report_logs(
    report_id: UUID,
    url: str = Query(..., min_length=1, description="URL exacta del reporte"),
    current_user: User | None = Depends(get_current_user_optional),
    session=Depends(get_session),
):
    del current_user
    report = await get_rich_results_report_service().get_report(
        session,
        report_id=report_id,
        url=url,
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    items = await get_task_progress_service().list_logs(
        session,
        task_type="rich_results_report",
        task_id=report_id,
    )
    return TaskLogListResponse(
        task_type="rich_results_report",
        task_id=report_id,
        items=[TaskLogEntryResponse.model_validate(item) for item in reversed(items)],
    )


@router.delete("/reports/{report_id}", response_model=DeleteRichResultsReportResponse)
async def delete_report_by_id(
    report_id: UUID,
    url: str = Query(..., min_length=1, description="URL exacta del reporte"),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    response = await get_rich_results_report_service().delete_report_by_id(
        session,
        report_id=report_id,
        user_id=current_user.id,
        url=url,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )
    return response


@router.delete("/reports", response_model=DeleteRichResultsReportResponse)
async def delete_reports_by_url(
    url: str = Query(..., min_length=1, description="URL exacta cuyos reportes se eliminarán"),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    response = await get_rich_results_report_service().delete_reports_by_url(
        session,
        url=url,
        user_id=current_user.id,
    )
    if response.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron reportes para la URL indicada",
        )
    return response
