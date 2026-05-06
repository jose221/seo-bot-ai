"""
Endpoints para generación de reportes de Google Rich Results.
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.rich_results_schemas import (
    RichResultsReportRequest,
    RichResultsReportResponse,
)
from app.services.rich_results_service import get_rich_results_service

router = APIRouter(prefix="/rich-results")


@router.post("/report-page", response_model=RichResultsReportResponse)
async def report_page(
    payload: RichResultsReportRequest,
    current_user: User = Depends(get_current_user),
):
    auth_token = getattr(current_user, "_token", None)
    return await get_rich_results_service().report_page(payload, token=auth_token)
