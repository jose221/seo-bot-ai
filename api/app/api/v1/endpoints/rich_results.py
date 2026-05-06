"""
Endpoints para generación de reportes de Google Rich Results.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.rich_results_schemas import (
    DeleteRichResultsReportResponse,
    RichResultsReportDetailResponse,
    RichResultsReportListResponse,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsScreenshot,
)
from app.services.rich_results_report_service import get_rich_results_report_service
from app.services.rich_results_service import get_rich_results_service

router = APIRouter(prefix="/rich-results")


@router.post("/report-page", response_model=RichResultsReportResponse)
async def report_page(
    payload: RichResultsReportRequest,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    auth_token = getattr(current_user, "_token", None)
    response = await get_rich_results_service().report_page(payload, token=auth_token)
    report = await get_rich_results_report_service().save_report(
        session,
        user_id=current_user.id,
        payload=payload,
        response=response,
    )

    if not report:
        return response

    return response.model_copy(update={"report_id": report.id, "saved": True})


@router.get("/get_reports", response_model=RichResultsReportListResponse)
async def get_reports(
    url: str | None = Query(None, description="Filtro parcial por URL"),
    distinct: bool = Query(
        False,
        description="Si es true, devuelve solo el reporte más reciente por URL",
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int | None = Query(None, ge=1, le=100, description="Elementos por página"),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    return await get_rich_results_report_service().list_reports(
        session,
        user_id=current_user.id,
        url=url,
        distinct=distinct,
        page=page,
        page_size=page_size,
    )


@router.get("/get_reports/{report_id}", response_model=RichResultsReportDetailResponse)
async def get_report_by_id(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    report = await get_rich_results_report_service().get_report(
        session,
        user_id=current_user.id,
        report_id=report_id,
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    ai_result = get_rich_results_report_service().build_ai_result(report)
    screenshots = [
        RichResultsScreenshot(**item)
        for item in (report.screenshots or [])
    ]
    return RichResultsReportDetailResponse(
        id=report.id,
        url=report.url,
        input_type=report.input_type,
        success=report.success,
        method_used=report.method_used,
        result_url=report.result_url,
        message=report.message,
        error_message=report.error_message,
        blocked_by_google=report.blocked_by_google,
        screenshots=screenshots,
        get_ai_result=ai_result,
        ai_error_message=report.ai_error_message,
        created_at=report.created_at,
    )


@router.delete("/reports/{report_id}", response_model=DeleteRichResultsReportResponse)
async def delete_report_by_id(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    response = await get_rich_results_report_service().delete_report_by_id(
        session,
        user_id=current_user.id,
        report_id=report_id,
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
        user_id=current_user.id,
        url=url,
    )
    if response.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron reportes para la URL indicada",
        )
    return response
