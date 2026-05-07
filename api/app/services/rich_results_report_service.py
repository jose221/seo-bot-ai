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
    RichResultsAnalysisFinding,
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportDetailResponse,
    RichResultsReportListItem,
    RichResultsReportListResponse,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsReportStatusSummaryItem,
    RichResultsReportStatusSummaryResponse,
    RichResultsScreenshot,
    RichResultsValidatorDetail,
)
from app.services.rich_results_service import get_rich_results_service
from app.services.task_progress_service import get_task_progress_service

log = logging.getLogger(__name__)


class RichResultsReportService:
    RETENTION_DAYS = 7
    CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
    BATCH_SCRAPING_CONCURRENCY = 7

    @staticmethod
    def _clamp_progress(progress: int) -> int:
        return max(0, min(100, int(progress)))

    @staticmethod
    def _log_progress(
        *,
        report_id: UUID,
        message: str,
        level: str = "info",
        progress_percentage: int | None = None,
    ) -> None:
        get_task_progress_service().log_sync(
            task_type="rich_results_report",
            task_id=report_id,
            message=message,
            level=level,
            progress_percentage=progress_percentage,
        )

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
            validate_google=response.validate_google,
            validate_schema_org=response.validate_schema_org,
            success=response.success,
            method_used=response.method_used,
            result_url=response.result_url,
            message=response.message,
            error_message=response.error_message,
            blocked_by_google=response.blocked_by_google,
            screenshots=[item.model_dump() for item in response.screenshots] or None,
            analysis_findings=[item.model_dump() for item in response.findings] or None,
            google_validation_result=response.google_validation.model_dump(),
            schema_org_validation_result=response.schema_org_validation.model_dump(),
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
            progress_percentage=0,
            progress_message="Reporte de validación estructurada en cola",
            input_type="url",
            requested_ai_result=payload.get_ai_result,
            validate_google=payload.validate_google,
            validate_schema_org=payload.validate_schema_org,
            success=False,
            method_used="queued",
            message="Reporte de validación estructurada en cola",
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        self._log_progress(
            report_id=report.id,
            message=f"Reporte en cola para {report.url}",
            progress_percentage=0,
        )
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
                RichResultsReport.progress_percentage,
                RichResultsReport.progress_message,
                RichResultsReport.input_type,
                RichResultsReport.requested_ai_result,
                RichResultsReport.validate_google,
                RichResultsReport.validate_schema_org,
                RichResultsReport.success,
                RichResultsReport.method_used,
                RichResultsReport.result_url,
                RichResultsReport.message,
                RichResultsReport.error_message,
                RichResultsReport.blocked_by_google,
                RichResultsReport.analysis_findings,
                RichResultsReport.google_validation_result,
                RichResultsReport.schema_org_validation_result,
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
                progress_percentage=row.progress_percentage,
                progress_message=row.progress_message,
                input_type=row.input_type,
                requested_ai_result=row.requested_ai_result,
                validate_google=row.validate_google,
                validate_schema_org=row.validate_schema_org,
                success=row.success,
                method_used=row.method_used,
                result_url=row.result_url,
                message=row.message,
                error_message=row.error_message,
                blocked_by_google=row.blocked_by_google,
                findings_summary=self._build_findings_summary(row.analysis_findings),
                google_validation=self.build_validator_detail(row.google_validation_result, "google"),
                schema_org_validation=self.build_validator_detail(row.schema_org_validation_result, "schema_org"),
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

    async def get_status_summaries(
        self,
        session,
        *,
        urls: list[str],
    ) -> RichResultsReportStatusSummaryResponse:
        normalized_urls = []
        seen_urls = set()

        for raw_url in urls:
            normalized = self._normalize_url(raw_url)
            if not normalized or normalized in seen_urls:
                continue
            normalized_urls.append(normalized)
            seen_urls.add(normalized)

        if not normalized_urls:
            return RichResultsReportStatusSummaryResponse(items=[])

        statement = (
            select(RichResultsReport)
            .where(RichResultsReport.url.in_(normalized_urls))
            .order_by(desc(RichResultsReport.created_at))
        )
        reports = (await session.execute(statement)).scalars().all()

        latest_by_url: dict[str, RichResultsReport] = {}
        for report in reports:
            if report.url not in latest_by_url:
                latest_by_url[report.url] = report

        items = []
        for url in normalized_urls:
            report = latest_by_url.get(url)
            state = self._classify_state(report)
            findings_summary = self._build_findings_summary(
                report.analysis_findings if report else None
            )
            items.append(
                RichResultsReportStatusSummaryItem(
                    url=url,
                    state=state,
                    report_id=report.id if report else None,
                    report_status=report.status if report else None,
                    progress_percentage=report.progress_percentage if report else 0,
                    progress_message=report.progress_message if report else None,
                    success=report.success if report else None,
                    blocked_by_google=report.blocked_by_google if report else None,
                    validate_google=report.validate_google if report else True,
                    validate_schema_org=report.validate_schema_org if report else True,
                    has_error=(
                        bool(report.error_message)
                        or findings_summary.by_severity.get("critical", 0) > 0
                        or findings_summary.by_severity.get("error", 0) > 0
                    ) if report else False,
                    message=report.message if report else None,
                    error_message=report.error_message if report else None,
                    findings_summary=findings_summary,
                    google_validation=self.build_validator_detail(
                        report.google_validation_result if report else None,
                        "google",
                    ),
                    schema_org_validation=self.build_validator_detail(
                        report.schema_org_validation_result if report else None,
                        "schema_org",
                    ),
                    created_at=report.created_at if report else None,
                )
            )

        return RichResultsReportStatusSummaryResponse(items=items)

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
                report.progress_percentage = 10
                report.progress_message = f"Iniciando validación Rich Results para {report.url}"
                report.method_used = "processing"
                report.message = "Generando reporte de validación estructurada"
                session.add(report)
            self._log_progress(
                report_id=report_id,
                message=f"Iniciando validación estructurada para {payload.content}",
                progress_percentage=10,
            )

            response = await get_rich_results_service().report_page(payload, token=token)

            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if report:
                    report.progress_percentage = 90 if payload.get_ai_result else 80
                    report.progress_message = (
                        "Los validadores terminaron; guardando resultado y análisis con IA"
                        if payload.get_ai_result
                        else "Los validadores terminaron; guardando resultado"
                    )
                    session.add(report)
            self._log_progress(
                report_id=report_id,
                message=(
                    "Los validadores terminaron; guardando resultado y análisis con IA"
                    if payload.get_ai_result
                    else "Los validadores terminaron; guardando resultado"
                ),
                progress_percentage=90 if payload.get_ai_result else 80,
            )

            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if not report:
                    return

                ai_result = response.get_ai_result
                report.status = RichResultsReportStatus.COMPLETED
                report.progress_percentage = 100
                report.progress_message = response.message
                report.input_type = response.input_type
                report.requested_ai_result = payload.get_ai_result
                report.validate_google = response.validate_google
                report.validate_schema_org = response.validate_schema_org
                report.success = response.success
                report.method_used = response.method_used
                report.result_url = response.result_url
                report.message = response.message
                report.error_message = response.error_message
                report.blocked_by_google = response.blocked_by_google
                report.screenshots = [item.model_dump() for item in response.screenshots] or None
                report.analysis_findings = [item.model_dump() for item in response.findings] or None
                report.google_validation_result = response.google_validation.model_dump()
                report.schema_org_validation_result = response.schema_org_validation.model_dump()
                report.ai_result_content = ai_result.content if ai_result else None
                report.ai_result_usage = ai_result.usage if ai_result else None
                report.ai_result_model = ai_result.model if ai_result else None
                report.ai_generated_at = ai_result.generated_at if ai_result else None
                report.ai_error_message = response.ai_error_message
                session.add(report)
            self._log_progress(
                report_id=report_id,
                message=response.message,
                progress_percentage=100,
            )
        except Exception as exc:
            log.exception("Error generando reporte Rich Results %s", report_id)
            with db_manager.sync_session_context() as session:
                report = session.get(RichResultsReport, report_id)
                if not report:
                    return
                report.status = RichResultsReportStatus.FAILED
                report.success = False
                report.progress_percentage = self._clamp_progress(report.progress_percentage or 0)
                report.progress_message = f"Error generando reporte: {exc}"
                report.method_used = "failed"
                report.message = "No fue posible generar el reporte de validación estructurada"
                report.error_message = str(exc)
                session.add(report)
            self._log_progress(
                report_id=report_id,
                message=f"Error generando reporte estructurado: {exc}",
                level="error",
            )

    async def run_batch_report_tasks(
        self,
        *,
        reports: list[tuple[UUID, RichResultsReportRequest]],
        token: str,
    ) -> None:
        semaphore = asyncio.Semaphore(self.BATCH_SCRAPING_CONCURRENCY)

        async def run_single_report(report_id: UUID, payload: RichResultsReportRequest) -> None:
            async with semaphore:
                await self.run_report_task(
                    report_id=report_id,
                    payload=payload,
                    token=token,
                )

        await asyncio.gather(
            *(run_single_report(report_id, payload) for report_id, payload in reports)
        )

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

    @staticmethod
    def build_findings(
        raw_findings: Optional[list[dict]],
    ) -> list[RichResultsAnalysisFinding]:
        if not raw_findings:
            return []

        findings: list[RichResultsAnalysisFinding] = []
        for item in raw_findings:
            try:
                findings.append(RichResultsAnalysisFinding.model_validate(item))
            except Exception:
                continue
        return findings

    @staticmethod
    def build_validator_detail(
        raw_validator_detail: Optional[dict],
        validator: str,
    ) -> RichResultsValidatorDetail:
        default_label = "Google Rich Results" if validator == "google" else "Schema.org Validator"
        if not raw_validator_detail:
            return RichResultsValidatorDetail(
                validator=validator,
                label=default_label,
                enabled=False,
                executed=False,
            )
        try:
            return RichResultsValidatorDetail.model_validate(raw_validator_detail)
        except Exception:
            return RichResultsValidatorDetail(
                validator=validator,
                label=default_label,
                enabled=False,
                executed=False,
            )

    def _build_findings_summary(
        self,
        raw_findings: Optional[list[dict]],
    ) -> RichResultsAnalysisSummary:
        return get_rich_results_service().build_findings_summary(
            self.build_findings(raw_findings)
        )

    def build_report_detail(self, report: RichResultsReport) -> RichResultsReportDetailResponse:
        ai_result = self.build_ai_result(report)
        findings = self.build_findings(report.analysis_findings)
        screenshots = [
            RichResultsScreenshot(**item)
            for item in (report.screenshots or [])
        ]
        return RichResultsReportDetailResponse(
            id=report.id,
            url=report.url,
            status=report.status,
            progress_percentage=report.progress_percentage,
            progress_message=report.progress_message,
            input_type=report.input_type,
            requested_ai_result=report.requested_ai_result,
            validate_google=report.validate_google,
            validate_schema_org=report.validate_schema_org,
            success=report.success,
            method_used=report.method_used,
            result_url=report.result_url,
            message=report.message,
            error_message=report.error_message,
            blocked_by_google=report.blocked_by_google,
            screenshots=screenshots,
            findings=findings,
            findings_summary=get_rich_results_service().build_findings_summary(findings),
            google_validation=self.build_validator_detail(report.google_validation_result, "google"),
            schema_org_validation=self.build_validator_detail(report.schema_org_validation_result, "schema_org"),
            get_ai_result=ai_result,
            ai_error_message=report.ai_error_message,
            created_at=report.created_at,
        )

    def _classify_state(self, report: Optional[RichResultsReport]) -> str:
        if report is None:
            return "none"

        if report.status in {RichResultsReportStatus.PENDING, RichResultsReportStatus.IN_PROGRESS}:
            return "pending"

        findings_summary = self._build_findings_summary(report.analysis_findings)
        severity_counts = findings_summary.by_severity

        if (
            report.status == RichResultsReportStatus.FAILED
            or report.error_message
            or severity_counts.get("critical", 0) > 0
            or severity_counts.get("error", 0) > 0
        ):
            return "error"

        if report.blocked_by_google or severity_counts.get("warning", 0) > 0:
            return "warning"

        if report.success:
            return "ok"

        return "warning"


_rich_results_report_service: Optional[RichResultsReportService] = None


def get_rich_results_report_service() -> RichResultsReportService:
    global _rich_results_report_service
    if _rich_results_report_service is None:
        _rich_results_report_service = RichResultsReportService()
    return _rich_results_report_service
