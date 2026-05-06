"""
Servicio para persistencia y limpieza de reportes de Google Rich Results.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import desc, select

from app.core.database import db_manager
from app.models.rich_results_report import RichResultsReport, RichResultsReportStatus
from app.schemas.rich_results_schemas import (
    DeleteRichResultsReportResponse,
    RichResultsAIResult,
    RichResultsReportDetailResponse,
    RichResultsReportListItem,
    RichResultsReportListResponse,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsScreenshot,
)
from app.services.rich_results_service import get_rich_results_service

log = logging.getLogger(__name__)


class RichResultsReportService:
    RETENTION_DAYS = 7
    CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60

    async def save_report(
        self,
        session,
        *,
        user_id: UUID,
        payload: RichResultsReportRequest,
        response: RichResultsReportResponse,
    ) -> Optional[RichResultsReport]:
        if not payload.is_url:
            return None

        ai_result = response.get_ai_result
        report = RichResultsReport(
            user_id=user_id,
            url=self._normalize_url(payload.content),
            input_type=response.input_type,
            success=response.success,
            method_used=response.method_used,
            result_url=response.result_url,
            message=response.message,
            error_message=response.error_message,
            blocked_by_google=response.blocked_by_google,
            screenshots=[item.model_dump() for item in response.screenshots] or None,
            ai_result_content=ai_result.content if ai_result else None,
            ai_result_usage=ai_result.usage if ai_result else None,
            ai_result_model=ai_result.model if ai_result else None,
            ai_generated_at=ai_result.generated_at if ai_result else None,
            ai_error_message=response.ai_error_message,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report

    async def create_pending_report(
        self,
        session,
        *,
        user_id: UUID,
        payload: RichResultsReportRequest,
    ) -> RichResultsReport:
        report = RichResultsReport(
            user_id=user_id,
            url=self._normalize_url(payload.content),
            status=RichResultsReportStatus.PENDING,
            input_type="url",
            requested_ai_result=payload.get_ai_result,
            success=False,
            method_used="queued",
            message="Reporte de Google Rich Results en cola",
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report

    async def list_reports(
        self,
        session,
        *,
        url: str,
        distinct: bool,
        page: int,
        page_size: Optional[int],
    ) -> RichResultsReportListResponse:
        normalized_url = self._normalize_url(url)
        base_statement = (
            select(
                RichResultsReport.id,
                RichResultsReport.url,
                RichResultsReport.status,
                RichResultsReport.input_type,
                RichResultsReport.requested_ai_result,
                RichResultsReport.success,
                RichResultsReport.method_used,
                RichResultsReport.result_url,
                RichResultsReport.message,
                RichResultsReport.error_message,
                RichResultsReport.blocked_by_google,
                RichResultsReport.created_at,
            )
            .order_by(desc(RichResultsReport.created_at))
        )
        count_statement = (
            select(func.count())
            .select_from(RichResultsReport)
            .where(RichResultsReport.url == normalized_url)
        )
        base_statement = base_statement.where(RichResultsReport.url == normalized_url)

        if distinct:
            rows = (await session.execute(base_statement)).all()
            latest_rows = []
            seen_urls = set()

            for row in rows:
                if row.url in seen_urls:
                    continue
                seen_urls.add(row.url)
                latest_rows.append(row)

            total = len(latest_rows)
            rows = self._paginate_rows(latest_rows, page=page, page_size=page_size)
        else:
            total = int((await session.execute(count_statement)).scalar() or 0)
            if page_size is not None:
                offset = (page - 1) * page_size
                base_statement = base_statement.offset(offset).limit(page_size)
            rows = (await session.execute(base_statement)).all()

        items = [
            RichResultsReportListItem(
                id=row.id,
                url=row.url,
                status=row.status,
                input_type=row.input_type,
                requested_ai_result=row.requested_ai_result,
                success=row.success,
                method_used=row.method_used,
                result_url=row.result_url,
                message=row.message,
                error_message=row.error_message,
                blocked_by_google=row.blocked_by_google,
                created_at=row.created_at,
            )
            for row in rows
        ]

        return RichResultsReportListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_report(
        self,
        session,
        *,
        report_id: UUID,
        url: str,
    ) -> Optional[RichResultsReport]:
        statement = select(RichResultsReport).where(
            RichResultsReport.id == report_id,
            RichResultsReport.url == self._normalize_url(url),
        )
        return (await session.execute(statement)).scalars().first()

    async def delete_report_by_id(
        self,
        session,
        *,
        report_id: UUID,
        user_id: UUID,
        url: str,
    ) -> Optional[DeleteRichResultsReportResponse]:
        report = (
            await session.execute(
                select(RichResultsReport).where(
                    RichResultsReport.id == report_id,
                    RichResultsReport.user_id == user_id,
                    RichResultsReport.url == self._normalize_url(url),
                )
            )
        ).scalars().first()
        if not report:
            return None

        await session.delete(report)
        await session.commit()
        return DeleteRichResultsReportResponse(
            success=True,
            message="Reporte eliminado exitosamente",
            deleted_count=1,
            report_id=report_id,
        )

    async def delete_reports_by_url(
        self,
        session,
        *,
        url: str,
        user_id: UUID,
    ) -> DeleteRichResultsReportResponse:
        normalized_url = self._normalize_url(url)
        statement = select(RichResultsReport).where(
            RichResultsReport.url == normalized_url,
            RichResultsReport.user_id == user_id,
        )
        reports = (await session.execute(statement)).scalars().all()

        for report in reports:
            await session.delete(report)
        await session.commit()

        return DeleteRichResultsReportResponse(
            success=True,
            message="Reportes eliminados exitosamente",
            deleted_count=len(reports),
            url=normalized_url,
        )

    async def run_report_task(
        self,
        *,
        report_id: UUID,
        payload: RichResultsReportRequest,
        token: str,
    ) -> None:
        try:
            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if not report:
                    return
                report.status = RichResultsReportStatus.IN_PROGRESS
                report.method_used = "processing"
                report.message = "Generando reporte de Google Rich Results"
                session.add(report)

            response = await get_rich_results_service().report_page(payload, token=token)

            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if not report:
                    return

                ai_result = response.get_ai_result
                report.status = RichResultsReportStatus.COMPLETED
                report.input_type = response.input_type
                report.requested_ai_result = payload.get_ai_result
                report.success = response.success
                report.method_used = response.method_used
                report.result_url = response.result_url
                report.message = response.message
                report.error_message = response.error_message
                report.blocked_by_google = response.blocked_by_google
                report.screenshots = [item.model_dump() for item in response.screenshots] or None
                report.ai_result_content = ai_result.content if ai_result else None
                report.ai_result_usage = ai_result.usage if ai_result else None
                report.ai_result_model = ai_result.model if ai_result else None
                report.ai_generated_at = ai_result.generated_at if ai_result else None
                report.ai_error_message = response.ai_error_message
                session.add(report)
        except Exception as exc:
            log.exception("Error generando reporte Rich Results %s", report_id)
            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if not report:
                    return
                report.status = RichResultsReportStatus.FAILED
                report.success = False
                report.method_used = "failed"
                report.message = "No fue posible generar el reporte de Google Rich Results"
                report.error_message = str(exc)
                session.add(report)

    async def run_cleanup_loop(self) -> None:
        while True:
            try:
                deleted = await asyncio.to_thread(self.cleanup_expired_reports)
                if deleted:
                    log.info("Rich Results cleanup completado: %s registro(s) eliminados", deleted)
            except Exception:
                log.exception("Error cleaning up expired Rich Results reports")

            await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)

    def cleanup_expired_reports(self) -> int:
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS)
        deleted = 0

        with db_manager.sync_session_context() as session:
            statement = select(RichResultsReport).where(RichResultsReport.created_at <= cutoff)
            reports = session.execute(statement).scalars().all()
            for report in reports:
                session.delete(report)
                deleted += 1

        return deleted

    @staticmethod
    def _normalize_url(value: str) -> str:
        return value.strip()

    @staticmethod
    def _paginate_rows(rows, *, page: int, page_size: Optional[int]):
        if page_size is None:
            return rows
        offset = (page - 1) * page_size
        return rows[offset:offset + page_size]

    @staticmethod
    def build_ai_result(report: RichResultsReport) -> Optional[RichResultsAIResult]:
        if (
            report.ai_result_content is None
            and report.ai_result_usage is None
            and report.ai_result_model is None
            and report.ai_generated_at is None
        ):
            return None

        return RichResultsAIResult(
            content=report.ai_result_content or "",
            usage=report.ai_result_usage,
            model=report.ai_result_model,
            generated_at=report.ai_generated_at,
        )

    def build_report_detail(self, report: RichResultsReport) -> RichResultsReportDetailResponse:
        ai_result = self.build_ai_result(report)
        screenshots = [
            RichResultsScreenshot(**item)
            for item in (report.screenshots or [])
        ]
        return RichResultsReportDetailResponse(
            id=report.id,
            url=report.url,
            status=report.status,
            input_type=report.input_type,
            requested_ai_result=report.requested_ai_result,
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


_rich_results_report_service: Optional[RichResultsReportService] = None


def get_rich_results_report_service() -> RichResultsReportService:
    global _rich_results_report_service
    if _rich_results_report_service is None:
        _rich_results_report_service = RichResultsReportService()
    return _rich_results_report_service
