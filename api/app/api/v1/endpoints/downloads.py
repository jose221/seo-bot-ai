"""
Endpoint opcional para servir archivos de reportes.
Permite descargar PDFs y Excel generados.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from uuid import UUID

from app.api.deps import get_current_user
from app.models.user import User
from app.models.audit import AuditReport
from app.models.audit_comparison import AuditComparison
from app.core.database import get_session
from sqlmodel import select

router = APIRouter()


@router.get("/audits/{audit_id}/download/pdf")
async def download_audit_pdf(
    audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Descargar el reporte PDF de una auditoría.
    """
    statement = select(AuditReport).where(
        AuditReport.id == audit_id,
        AuditReport.user_id == current_user.id
    )
    result = await session.execute(statement)
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )

    if not audit.report_pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte PDF no disponible"
        )

    file_path = Path(audit.report_pdf_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name
    )


@router.get("/audits/{audit_id}/download/excel")
async def download_audit_excel(
    audit_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Descargar el reporte Excel de una auditoría.
    """
    statement = select(AuditReport).where(
        AuditReport.id == audit_id,
        AuditReport.user_id == current_user.id
    )
    result = await session.execute(statement)
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )

    if not audit.report_excel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte Excel no disponible"
        )

    file_path = Path(audit.report_excel_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path.name
    )


@router.get("/audits/comparisons/{comparison_id}/download/pdf")
async def download_comparison_pdf(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Descargar el reporte PDF de una comparación.
    """
    statement = select(AuditComparison).where(
        AuditComparison.id == comparison_id,
        AuditComparison.user_id == current_user.id
    )
    result = await session.execute(statement)
    comparison = result.scalars().first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada"
        )

    if not comparison.report_pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte PDF no disponible"
        )

    file_path = Path(comparison.report_pdf_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name
    )


@router.get("/audits/comparisons/{comparison_id}/download/excel")
async def download_comparison_excel(
    comparison_id: UUID,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Descargar el reporte Excel de una comparación.
    """
    statement = select(AuditComparison).where(
        AuditComparison.id == comparison_id,
        AuditComparison.user_id == current_user.id
    )
    result = await session.execute(statement)
    comparison = result.scalars().first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada"
        )

    if not comparison.report_excel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte Excel no disponible"
        )

    file_path = Path(comparison.report_excel_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path.name
    )

