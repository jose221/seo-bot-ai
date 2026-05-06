"""
Endpoints para descargar reportes generados.
Regeneran PDF/Word bajo demanda cuando el archivo no existe o expiró.
"""
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models import AuditComparison, AuditReport, AuditSchemaReview, AuditUrlValidation
from app.models.user import User
from app.services.report_lifecycle import get_report_lifecycle_service

router = APIRouter()

report_lifecycle = get_report_lifecycle_service()


def _build_download_response(file_path: str, media_type: str) -> FileResponse:
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor",
        )
    return FileResponse(path=str(path), media_type=media_type, filename=path.name)


def _raise_generation_error(exc: ValueError) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    ) from exc


async def _get_owned_audit(session, audit_id: UUID, current_user: User) -> AuditReport:
    statement = select(AuditReport).where(
        AuditReport.id == audit_id,
        AuditReport.user_id == current_user.id,
    )
    result = await session.execute(statement)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada",
        )
    return audit


async def _get_owned_comparison(session, comparison_id: UUID, current_user: User) -> AuditComparison:
    statement = select(AuditComparison).where(
        AuditComparison.id == comparison_id,
        AuditComparison.user_id == current_user.id,
    )
    result = await session.execute(statement)
    comparison = result.scalars().first()
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada",
        )
    return comparison


async def _get_owned_schema_audit(
    session,
    schema_audit_id: UUID,
    current_user: User,
) -> AuditSchemaReview:
    statement = select(AuditSchemaReview).where(
        AuditSchemaReview.id == schema_audit_id,
        AuditSchemaReview.user_id == current_user.id,
    )
    result = await session.execute(statement)
    schema_audit = result.scalars().first()
    if not schema_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría de schemas no encontrada",
        )
    return schema_audit


async def _get_owned_url_validation(
    session,
    validation_id: UUID,
    current_user: User,
) -> AuditUrlValidation:
    statement = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    result = await session.execute(statement)
    validation = result.scalars().first()
    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación de URLs no encontrada",
        )
    return validation


@router.get("/audits/{audit_id}/download/pdf")
async def download_audit_pdf(
    audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    audit = await _get_owned_audit(session, audit_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_audit_pdf(session, audit)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/{audit_id}/download/word")
async def download_audit_word(
    audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    audit = await _get_owned_audit(session, audit_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_audit_word(session, audit)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/audits/{audit_id}/download/excel")
async def download_audit_excel(
    audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    audit = await _get_owned_audit(session, audit_id, current_user)
    if not audit.report_excel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte Excel no disponible",
        )
    return _build_download_response(
        audit.report_excel_path,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/audits/comparisons/{comparison_id}/download/pdf")
async def download_comparison_pdf(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    comparison = await _get_owned_comparison(session, comparison_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_comparison_pdf(session, comparison)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/comparisons/{comparison_id}/download/word")
async def download_comparison_word(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    comparison = await _get_owned_comparison(session, comparison_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_comparison_word(session, comparison)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/audits/comparisons/{comparison_id}/download/excel")
async def download_comparison_excel(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    comparison = await _get_owned_comparison(session, comparison_id, current_user)
    if not comparison.report_excel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte Excel no disponible",
        )
    return _build_download_response(
        comparison.report_excel_path,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/audits/comparisons/{comparison_id}/proposal/download/pdf")
async def download_comparison_proposal_pdf(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    comparison = await _get_owned_comparison(session, comparison_id, current_user)
    token = getattr(current_user, "_token", None)
    try:
        file_path = await report_lifecycle.ensure_comparison_proposal_pdf(session, comparison, token)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/comparisons/{comparison_id}/proposal/download/word")
async def download_comparison_proposal_word(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    comparison = await _get_owned_comparison(session, comparison_id, current_user)
    token = getattr(current_user, "_token", None)
    try:
        file_path = await report_lifecycle.ensure_comparison_proposal_word(session, comparison, token)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/audits/schemas/{schema_audit_id}/download/pdf")
async def download_schema_audit_pdf(
    schema_audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    schema_audit = await _get_owned_schema_audit(session, schema_audit_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_schema_pdf(session, schema_audit)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/schemas/{schema_audit_id}/download/word")
async def download_schema_audit_word(
    schema_audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    schema_audit = await _get_owned_schema_audit(session, schema_audit_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_schema_word(session, schema_audit)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/audits/url-validations/{validation_id}/download/pdf")
async def download_url_validation_pdf(
    validation_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    validation = await _get_owned_url_validation(session, validation_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_url_validation_pdf(session, validation)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/url-validations/{validation_id}/download/word")
async def download_url_validation_word(
    validation_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    validation = await _get_owned_url_validation(session, validation_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_url_validation_word(session, validation)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/audits/url-validations/{validation_id}/global/download/pdf")
async def download_url_validation_global_pdf(
    validation_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    validation = await _get_owned_url_validation(session, validation_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_url_validation_global_pdf(session, validation)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(file_path, "application/pdf")


@router.get("/audits/url-validations/{validation_id}/global/download/word")
async def download_url_validation_global_word(
    validation_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    validation = await _get_owned_url_validation(session, validation_id, current_user)
    try:
        file_path = await report_lifecycle.ensure_url_validation_global_word(session, validation)
    except ValueError as exc:
        _raise_generation_error(exc)
    return _build_download_response(
        file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
