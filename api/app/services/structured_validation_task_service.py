from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import desc, select

from app.core.database import db_manager
from app.models.rich_results_report import RichResultsReport
from app.models.structured_validation_task import (
    StructuredValidationInputMode,
    StructuredValidationTask,
    StructuredValidationTaskStatus,
)
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsValidatorDetail,
)
from app.schemas.structured_validation_schemas import (
    StructuredValidationCreateRequest,
    StructuredValidationTaskItem,
    StructuredValidationTaskListItem,
    StructuredValidationTaskListResponse,
    StructuredValidationTaskResponse,
)
from app.services.rich_results_report_service import get_rich_results_report_service
from app.services.rich_results_service import get_rich_results_service
from app.services.task_progress_service import get_task_progress_service

log = logging.getLogger(__name__)


class StructuredValidationTaskService:
    TASK_TYPE = "structured_validation_task"
    BATCH_CONCURRENCY = 7
    CONTROL_POLL_SECONDS = 1.0
    ACTIVE_STATUSES = {
        StructuredValidationTaskStatus.PENDING,
        StructuredValidationTaskStatus.IN_PROGRESS,
        StructuredValidationTaskStatus.PAUSED,
    }
    FINAL_STATUSES = {
        StructuredValidationTaskStatus.COMPLETED,
        StructuredValidationTaskStatus.FAILED,
        StructuredValidationTaskStatus.CANCELLED,
    }

    @staticmethod
    def _legacy_task_kind() -> str:
        return "rich_results_report"

    @staticmethod
    def _clamp_progress(progress: int) -> int:
        return max(0, min(100, int(progress)))

    @staticmethod
    def _normalize_sort_datetime(value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _split_urls(raw_urls: str) -> List[str]:
        seen = set()
        values: List[str] = []
        for token in (raw_urls or "").replace(",", " ").split():
            url = token.strip()
            if not url or url in seen:
                continue
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"URL invalida: {url}")
            seen.add(url)
            values.append(url)
        if not values:
            raise ValueError("Debes proporcionar al menos una URL valida")
        return values

    @staticmethod
    def _build_inputs(payload: StructuredValidationCreateRequest) -> List[Dict[str, Any]]:
        if payload.input_mode == StructuredValidationInputMode.URL:
            return [
                {
                    "item_key": url,
                    "label": url,
                    "value": url,
                    "input_type": StructuredValidationInputMode.URL.value,
                }
                for url in StructuredValidationTaskService._split_urls(payload.raw_urls or "")
            ]
        items: List[Dict[str, Any]] = []
        for index, html in enumerate(payload.html_items, start=1):
            item_key = f"html-{index}"
            items.append(
                {
                    "item_key": item_key,
                    "label": f"HTML #{index}",
                    "value": html,
                    "input_type": StructuredValidationInputMode.HTML.value,
                }
            )
        return items

    @staticmethod
    def _derive_item_severity(report: RichResultsReportResponse) -> str:
        summary = report.findings_summary.by_severity or {}
        if summary.get("critical") or summary.get("error"):
            return "critical"
        if summary.get("warning"):
            return "warning"
        if report.success:
            return "ok"
        return "error"

    @classmethod
    def _item_preview(cls, input_type: StructuredValidationInputMode, value: str) -> str:
        if input_type == StructuredValidationInputMode.URL:
            return value
        compact = " ".join(value.split())
        return compact[:220] + ("..." if len(compact) > 220 else "")

    @classmethod
    def _serialize_result(
        cls,
        *,
        item_key: str,
        label: str,
        input_type: StructuredValidationInputMode,
        source_value: str,
        report: RichResultsReportResponse,
    ) -> Dict[str, Any]:
        return {
            "item_key": item_key,
            "label": label,
            "input_type": input_type.value,
            "source_value": source_value,
            "source_preview": cls._item_preview(input_type, source_value),
            "success": report.success,
            "severity": cls._derive_item_severity(report),
            "message": report.message,
            "error_message": report.error_message,
            "report": report.model_dump(mode="json"),
        }

    @classmethod
    def _deserialize_item(cls, raw: Dict[str, Any]) -> StructuredValidationTaskItem:
        report_payload = raw.get("report") or {}
        return StructuredValidationTaskItem(
            item_key=raw.get("item_key", ""),
            input_type=StructuredValidationInputMode(raw.get("input_type", StructuredValidationInputMode.URL.value)),
            label=raw.get("label", ""),
            source_preview=raw.get("source_preview"),
            source_value=raw.get("source_value"),
            success=bool(raw.get("success")),
            severity=raw.get("severity"),
            message=raw.get("message"),
            error_message=raw.get("error_message"),
            report=RichResultsReportResponse.model_validate(report_payload),
        )

    @staticmethod
    def _build_placeholder_report(
        *,
        input_type: StructuredValidationInputMode,
        validate_google: bool,
        validate_schema_org: bool,
        task_status: StructuredValidationTaskStatus,
    ) -> RichResultsReportResponse:
        waiting_message = (
            "Pendiente de procesamiento"
            if task_status == StructuredValidationTaskStatus.PENDING
            else "Pausado"
            if task_status == StructuredValidationTaskStatus.PAUSED
            else "Procesándose"
        )
        return RichResultsReportResponse(
            success=False,
            input_type=input_type.value,
            method_used="queued",
            result_url=None,
            message=waiting_message,
            error_message=None,
            blocked_by_google=False,
            validate_google=validate_google,
            validate_schema_org=validate_schema_org,
            screenshots=[],
            findings=[],
            findings_summary=RichResultsAnalysisSummary(),
            google_validation=RichResultsValidatorDetail(
                validator="google",
                label="Google Rich Results",
                enabled=validate_google,
                executed=False,
            ),
            schema_org_validation=RichResultsValidatorDetail(
                validator="schema_org",
                label="Schema.org Validator",
                enabled=validate_schema_org,
                executed=False,
            ),
            get_ai_result=None,
            ai_error_message=None,
            report_id=None,
            saved=False,
        )

    def _build_pending_task_item(
        self,
        *,
        raw_input: Dict[str, Any],
        task: StructuredValidationTask,
    ) -> StructuredValidationTaskItem:
        input_type = StructuredValidationInputMode(
            raw_input.get("input_type", StructuredValidationInputMode.URL.value)
        )
        source_value = raw_input.get("value") or ""
        label = raw_input.get("label") or raw_input.get("item_key") or source_value or "Elemento"
        return StructuredValidationTaskItem(
            item_key=raw_input.get("item_key", ""),
            input_type=input_type,
            label=label,
            source_preview=self._item_preview(input_type, source_value),
            source_value=source_value,
            success=False,
            severity=None,
            message="Pendiente de procesamiento",
            error_message=None,
            report=self._build_placeholder_report(
                input_type=input_type,
                validate_google=task.validate_google,
                validate_schema_org=task.validate_schema_org,
                task_status=task.status,
            ),
        )

    @staticmethod
    def _build_failed_report(
        *,
        input_type: StructuredValidationInputMode,
        validate_google: bool,
        validate_schema_org: bool,
        message: str,
    ) -> RichResultsReportResponse:
        return RichResultsReportResponse(
            success=False,
            input_type=input_type.value,
            method_used="error",
            result_url=None,
            message=message,
            error_message=message,
            blocked_by_google=False,
            validate_google=validate_google,
            validate_schema_org=validate_schema_org,
            screenshots=[],
            findings=[],
            findings_summary=RichResultsAnalysisSummary(),
            google_validation=RichResultsValidatorDetail(
                validator="google",
                label="Google Rich Results",
                enabled=validate_google,
                executed=False,
                error_message=message if validate_google else None,
            ),
            schema_org_validation=RichResultsValidatorDetail(
                validator="schema_org",
                label="Schema.org Validator",
                enabled=validate_schema_org,
                executed=False,
                error_message=message if validate_schema_org else None,
            ),
            get_ai_result=None,
            ai_error_message=None,
            report_id=None,
            saved=False,
        )

    def _build_embedded_legacy_report(self, report: RichResultsReport) -> RichResultsReportResponse:
        report_service = get_rich_results_report_service()
        findings = report_service.build_findings(report.analysis_findings)
        screenshots = list(report.screenshots or [])
        ai_result = report_service.build_ai_result(report)
        return RichResultsReportResponse(
            success=report.success,
            input_type=report.input_type,
            method_used=report.method_used,
            result_url=report.result_url,
            message=report.message,
            error_message=report.error_message,
            blocked_by_google=report.blocked_by_google,
            validate_google=report.validate_google,
            validate_schema_org=report.validate_schema_org,
            screenshots=screenshots,
            findings=findings,
            findings_summary=get_rich_results_service().build_findings_summary(findings),
            google_validation=report_service.build_validator_detail(report.google_validation_result, "google"),
            schema_org_validation=report_service.build_validator_detail(report.schema_org_validation_result, "schema_org"),
            get_ai_result=RichResultsAIResult.model_validate(ai_result.model_dump()) if ai_result else None,
            ai_error_message=report.ai_error_message,
            report_id=report.id,
            saved=True,
        )

    def _build_legacy_list_item(self, report: RichResultsReport) -> StructuredValidationTaskListItem:
        report_status = str(report.status)
        is_pending = report_status in {"pending", "in_progress"}
        is_finished = report_status in {"completed", "failed"}
        return StructuredValidationTaskListItem(
            id=report.id,
            task_kind=self._legacy_task_kind(),
            supports_runtime_control=False,
            input_mode=StructuredValidationInputMode.URL,
            name=report.url,
            description=report.message,
            status=report.status,
            progress_percentage=report.progress_percentage,
            progress_message=report.progress_message,
            total_items=1,
            completed_items=0 if is_pending else 1,
            successful_items=1 if report.success else 0,
            failed_items=1 if report_status == "failed" or (not report.success and report_status == "completed") else 0,
            validate_google=report.validate_google,
            validate_schema_org=report.validate_schema_org,
            requested_ai_result=report.requested_ai_result,
            created_at=report.created_at,
            completed_at=report.created_at if is_finished else None,
        )

    def _build_legacy_task_response(self, report: RichResultsReport) -> StructuredValidationTaskResponse:
        embedded_report = self._build_embedded_legacy_report(report)
        report_status = str(report.status)
        is_pending = report_status in {"pending", "in_progress"}
        is_finished = report_status in {"completed", "failed"}
        return StructuredValidationTaskResponse(
            id=report.id,
            task_kind=self._legacy_task_kind(),
            supports_runtime_control=False,
            input_mode=StructuredValidationInputMode.URL,
            name=report.url,
            description=report.message,
            ai_instruction=None,
            requested_ai_result=report.requested_ai_result,
            auto_extract_html=False,
            validate_google=report.validate_google,
            validate_schema_org=report.validate_schema_org,
            status=report.status,
            progress_percentage=report.progress_percentage,
            progress_message=report.progress_message,
            total_items=1,
            completed_items=0 if is_pending else 1,
            successful_items=1 if report.success else 0,
            failed_items=1 if report_status == "failed" or (not report.success and report_status == "completed") else 0,
            success=report.success,
            message=report.message,
            error_message=report.error_message,
            created_at=report.created_at,
            updated_at=report.created_at,
            completed_at=report.created_at if is_finished else None,
            items=[
                StructuredValidationTaskItem(
                    item_key=report.url,
                    input_type=StructuredValidationInputMode.URL,
                    label=report.url,
                    source_preview=report.url,
                    source_value=report.url,
                    success=report.success,
                    severity=self._derive_item_severity(embedded_report),
                    message=report.message,
                    error_message=report.error_message,
                    report=embedded_report,
                )
            ],
        )

    @staticmethod
    def _log_progress(task_id: UUID, message: str, level: str = "info", progress_percentage: Optional[int] = None) -> None:
        get_task_progress_service().log_sync(
            task_type=StructuredValidationTaskService.TASK_TYPE,
            task_id=task_id,
            message=message,
            level=level,
            progress_percentage=progress_percentage,
        )

    async def _reload_task(self, session, task_id: UUID) -> Optional[StructuredValidationTask]:
        session.expire_all()
        return await self.get_task(session, task_id=task_id)

    async def _get_runtime_status(self, task_id: UUID) -> Optional[StructuredValidationTaskStatus]:
        async with db_manager.async_session_context() as control_session:
            task = await self.get_task(control_session, task_id=task_id)
            return task.status if task else None

    async def _wait_until_resumable(self, task_id: UUID) -> Optional[StructuredValidationTaskStatus]:
        while True:
            status = await self._get_runtime_status(task_id)
            if status is None or status != StructuredValidationTaskStatus.PAUSED:
                return status
            await asyncio.sleep(self.CONTROL_POLL_SECONDS)

    async def _set_task_status(
        self,
        session,
        *,
        task: StructuredValidationTask,
        status_value: StructuredValidationTaskStatus,
        message: str,
        progress_message: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> StructuredValidationTask:
        task.status = status_value
        task.message = message
        task.progress_message = progress_message if progress_message is not None else message
        task.error_message = error_message
        task.success = False if status_value in {StructuredValidationTaskStatus.FAILED, StructuredValidationTaskStatus.CANCELLED} else task.success
        task.updated_at = datetime.utcnow()
        task.completed_at = completed_at
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def pause_task(self, session, *, task: StructuredValidationTask) -> StructuredValidationTask:
        if task.status == StructuredValidationTaskStatus.PAUSED:
            return task
        if task.status not in {StructuredValidationTaskStatus.PENDING, StructuredValidationTaskStatus.IN_PROGRESS}:
            raise ValueError("Solo se pueden pausar tareas pendientes o en progreso")
        paused_message = "Tarea pausada manualmente"
        await self._set_task_status(
            session,
            task=task,
            status_value=StructuredValidationTaskStatus.PAUSED,
            message=paused_message,
            progress_message=paused_message,
            completed_at=None,
        )
        self._log_progress(task.id, paused_message, level="warning", progress_percentage=task.progress_percentage)
        return task

    async def resume_task(self, session, *, task: StructuredValidationTask) -> StructuredValidationTask:
        if task.status == StructuredValidationTaskStatus.IN_PROGRESS:
            return task
        if task.status != StructuredValidationTaskStatus.PAUSED:
            raise ValueError("Solo se pueden reanudar tareas pausadas")
        resume_message = "Tarea reanudada manualmente"
        await self._set_task_status(
            session,
            task=task,
            status_value=StructuredValidationTaskStatus.IN_PROGRESS,
            message=resume_message,
            progress_message=resume_message,
            completed_at=None,
        )
        self._log_progress(task.id, resume_message, level="info", progress_percentage=task.progress_percentage)
        return task

    async def cancel_task(self, session, *, task: StructuredValidationTask) -> StructuredValidationTask:
        if task.status == StructuredValidationTaskStatus.CANCELLED:
            return task
        if task.status not in self.ACTIVE_STATUSES:
            raise ValueError("Solo se pueden cancelar tareas activas")
        cancel_message = "Tarea cancelada manualmente"
        await self._set_task_status(
            session,
            task=task,
            status_value=StructuredValidationTaskStatus.CANCELLED,
            message=cancel_message,
            progress_message=cancel_message,
            completed_at=datetime.utcnow(),
        )
        self._log_progress(task.id, cancel_message, level="warning", progress_percentage=task.progress_percentage)
        return task

    async def create_task(
        self,
        session,
        *,
        user_id: UUID,
        payload: StructuredValidationCreateRequest,
    ) -> StructuredValidationTask:
        inputs = self._build_inputs(payload)
        task = StructuredValidationTask(
            user_id=user_id,
            input_mode=payload.input_mode,
            name=payload.name,
            description=payload.description,
            ai_instruction=payload.ai_instruction,
            requested_ai_result=payload.get_ai_result,
            auto_extract_html=payload.auto_extract_html,
            validate_google=payload.validate_google,
            validate_schema_org=payload.validate_schema_org,
            status=StructuredValidationTaskStatus.PENDING,
            progress_percentage=0,
            progress_message="Tarea en cola",
            total_items=len(inputs),
            inputs_json=inputs,
            results_json=[],
            message="Tarea de validacion estructurada en cola",
            success=False,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        self._log_progress(task.id, f"Tarea creada con {len(inputs)} elementos", progress_percentage=0)
        return task

    async def rerun_task(self, session, *, task: StructuredValidationTask) -> StructuredValidationTask:
        task.status = StructuredValidationTaskStatus.PENDING
        task.progress_percentage = 0
        task.progress_message = "Tarea en cola"
        task.completed_items = 0
        task.successful_items = 0
        task.failed_items = 0
        task.results_json = []
        task.success = False
        task.error_message = None
        task.message = "Tarea de validacion estructurada en cola"
        task.updated_at = datetime.utcnow()
        task.completed_at = None
        session.add(task)
        await session.commit()
        await session.refresh(task)
        self._log_progress(task.id, "Reejecucion encolada", progress_percentage=0)
        return task

    async def list_tasks(
        self,
        session,
        *,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> StructuredValidationTaskListResponse:
        fetch_limit = max(page * page_size, page_size)
        task_total = int(
            (await session.execute(
                select(func.count()).select_from(StructuredValidationTask).where(
                    StructuredValidationTask.user_id == user_id
                )
            )).scalar() or 0
        )
        legacy_total = int(
            (await session.execute(
                select(func.count()).select_from(RichResultsReport).where(
                    RichResultsReport.user_id == user_id
                )
            )).scalar() or 0
        )

        task_items = (
            await session.execute(
                select(StructuredValidationTask)
                .where(StructuredValidationTask.user_id == user_id)
                .order_by(desc(StructuredValidationTask.created_at))
                .limit(fetch_limit)
            )
        ).scalars().all()
        legacy_reports = (
            await session.execute(
                select(RichResultsReport)
                .where(RichResultsReport.user_id == user_id)
                .order_by(desc(RichResultsReport.created_at))
                .limit(fetch_limit)
            )
        ).scalars().all()

        combined_items = [
            *[
                StructuredValidationTaskListItem(
                    id=item.id,
                    task_kind=self.TASK_TYPE,
                    supports_runtime_control=True,
                    input_mode=item.input_mode,
                    name=item.name,
                    description=item.description,
                    status=item.status,
                    progress_percentage=item.progress_percentage,
                    progress_message=item.progress_message,
                    total_items=item.total_items,
                    completed_items=item.completed_items,
                    successful_items=item.successful_items,
                    failed_items=item.failed_items,
                    validate_google=item.validate_google,
                    validate_schema_org=item.validate_schema_org,
                    requested_ai_result=item.requested_ai_result,
                    created_at=item.created_at,
                    completed_at=item.completed_at,
                )
                for item in task_items
            ],
            *[self._build_legacy_list_item(report) for report in legacy_reports],
        ]
        combined_items.sort(
            key=lambda item: self._normalize_sort_datetime(item.created_at),
            reverse=True,
        )
        total = task_total + legacy_total
        start = (page - 1) * page_size
        end = start + page_size
        return StructuredValidationTaskListResponse(
            items=combined_items[start:end],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_task(self, session, *, task_id: UUID, user_id: Optional[UUID] = None) -> Optional[StructuredValidationTask]:
        stmt = select(StructuredValidationTask).where(StructuredValidationTask.id == task_id)
        if user_id is not None:
            stmt = stmt.where(StructuredValidationTask.user_id == user_id)
        return (await session.execute(stmt)).scalars().first()

    async def get_legacy_report(self, session, *, task_id: UUID, user_id: Optional[UUID] = None) -> Optional[RichResultsReport]:
        stmt = select(RichResultsReport).where(RichResultsReport.id == task_id)
        if user_id is not None:
            stmt = stmt.where(RichResultsReport.user_id == user_id)
        return (await session.execute(stmt)).scalars().first()

    def build_task_response(self, task: StructuredValidationTask) -> StructuredValidationTaskResponse:
        completed_items_by_key = {
            item.get("item_key", ""): self._deserialize_item(item)
            for item in (task.results_json or [])
            if item.get("item_key")
        }
        ordered_items: List[StructuredValidationTaskItem] = []
        for raw_input in (task.inputs_json or []):
            item_key = raw_input.get("item_key", "")
            ordered_items.append(
                completed_items_by_key.get(item_key)
                or self._build_pending_task_item(raw_input=raw_input, task=task)
            )
        return StructuredValidationTaskResponse(
            id=task.id,
            task_kind=self.TASK_TYPE,
            supports_runtime_control=True,
            input_mode=task.input_mode,
            name=task.name,
            description=task.description,
            ai_instruction=task.ai_instruction,
            requested_ai_result=task.requested_ai_result,
            auto_extract_html=task.auto_extract_html,
            validate_google=task.validate_google,
            validate_schema_org=task.validate_schema_org,
            status=task.status,
            progress_percentage=task.progress_percentage,
            progress_message=task.progress_message,
            total_items=task.total_items,
            completed_items=task.completed_items,
            successful_items=task.successful_items,
            failed_items=task.failed_items,
            success=task.success,
            message=task.message,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            items=ordered_items,
        )

    def build_legacy_response(self, report: RichResultsReport) -> StructuredValidationTaskResponse:
        return self._build_legacy_task_response(report)

    async def delete_task(self, session, *, task: StructuredValidationTask) -> None:
        await session.delete(task)
        await session.commit()

    async def run_task(self, *, task_id: UUID, token: str = "") -> None:
        async with db_manager.async_session_context() as session:
            task = await self.get_task(session, task_id=task_id)
            if not task:
                return
            try:
                if task.status == StructuredValidationTaskStatus.CANCELLED:
                    return
                if task.status == StructuredValidationTaskStatus.PENDING:
                    task.status = StructuredValidationTaskStatus.IN_PROGRESS
                    task.progress_percentage = max(task.progress_percentage, 5)
                    task.message = "Tarea en progreso"
                    task.progress_message = "Iniciando validaciones"
                    task.updated_at = datetime.utcnow()
                    task.completed_at = None
                    session.add(task)
                    await session.commit()
                    self._log_progress(task.id, "Iniciando validacion de elementos", progress_percentage=task.progress_percentage)

                total = max(1, len(task.inputs_json or []))
                results_by_key: Dict[str, Dict[str, Any]] = {
                    item.get("item_key", ""): item
                    for item in (task.results_json or [])
                    if item.get("item_key")
                }
                completed_items = len(results_by_key)
                successful_items = sum(1 for item in results_by_key.values() if item.get("success"))
                pending_inputs = [
                    (index, item)
                    for index, item in enumerate(task.inputs_json or [], start=1)
                    if (item.get("item_key") or item.get("label") or "") not in results_by_key
                ]
                pending_queue: asyncio.Queue[tuple[int, Dict[str, Any]]] = asyncio.Queue()
                for entry in pending_inputs:
                    pending_queue.put_nowait(entry)

                update_lock = asyncio.Lock()

                async def process_item(index: int, item: Dict[str, Any]) -> tuple[str, str, Dict[str, Any], bool]:
                    input_type = StructuredValidationInputMode(
                        item.get("input_type", StructuredValidationInputMode.URL.value)
                    )
                    label = item.get("label") or item.get("item_key") or f"Elemento {index}"
                    source_value = item.get("value") or ""
                    item_key = item.get("item_key") or label

                    self._log_progress(
                        task.id,
                        f"Procesando {label}",
                        progress_percentage=self._clamp_progress(int((max(completed_items, 0) / total) * 100)),
                    )
                    try:
                        report_payload = RichResultsReportRequest(
                            content=source_value,
                            is_url=input_type == StructuredValidationInputMode.URL,
                            get_ai_result=task.requested_ai_result,
                            auto_extract_html=task.auto_extract_html if input_type == StructuredValidationInputMode.URL else False,
                            validate_google=task.validate_google,
                            validate_schema_org=task.validate_schema_org,
                        )
                        report = await get_rich_results_service().report_page(report_payload, token=token)
                    except Exception as exc:
                        log.exception("Error procesando elemento %s de structured task %s", label, task.id)
                        report = self._build_failed_report(
                            input_type=input_type,
                            validate_google=task.validate_google,
                            validate_schema_org=task.validate_schema_org,
                            message=str(exc),
                        )
                    serialized = self._serialize_result(
                        item_key=item_key,
                        label=label,
                        input_type=input_type,
                        source_value=source_value,
                        report=report,
                    )
                    return item_key, label, serialized, report.success

                async def worker() -> None:
                    nonlocal completed_items, successful_items, task
                    while True:
                        runtime_status = await self._wait_until_resumable(task.id)
                        if runtime_status is None or runtime_status == StructuredValidationTaskStatus.CANCELLED:
                            return
                        try:
                            index, item = pending_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            return

                        item_key, label, serialized, success = await process_item(index, item)

                        async with update_lock:
                            results_by_key[item_key] = serialized
                            completed_items += 1
                            if success:
                                successful_items += 1

                            report_message = serialized.get("message") or "Elemento procesado"
                            progress_value = self._clamp_progress(int((completed_items / total) * 100))
                            self._log_progress(
                                task.id,
                                f"{label}: {report_message}",
                                level="success" if success else "warning",
                                progress_percentage=progress_value,
                            )

                            task = await self._reload_task(session, task.id)
                            if not task:
                                return

                            ordered_results = [
                                results_by_key[item.get("item_key") or item.get("label") or ""]
                                for item in (task.inputs_json or [])
                                if (item.get("item_key") or item.get("label") or "") in results_by_key
                            ]
                            task.results_json = ordered_results
                            task.completed_items = completed_items
                            task.successful_items = successful_items
                            task.failed_items = completed_items - successful_items
                            task.progress_percentage = progress_value
                            task.updated_at = datetime.utcnow()

                            current_status = task.status
                            if current_status == StructuredValidationTaskStatus.CANCELLED:
                                task.message = "Tarea cancelada manualmente"
                                task.progress_message = "Tarea cancelada manualmente"
                                task.completed_at = task.completed_at or datetime.utcnow()
                                task.success = False
                            elif current_status == StructuredValidationTaskStatus.PAUSED:
                                task.message = "Tarea pausada manualmente"
                                task.progress_message = "Tarea pausada manualmente"
                                task.completed_at = None
                            else:
                                task.status = StructuredValidationTaskStatus.IN_PROGRESS
                                task.message = "Tarea en progreso"
                                task.progress_message = f"Procesados {completed_items} de {total} elementos"
                                task.completed_at = None

                            session.add(task)
                            await session.commit()

                workers = [
                    asyncio.create_task(worker())
                    for _ in range(max(1, min(self.BATCH_CONCURRENCY, len(pending_inputs) or 1)))
                ]
                await asyncio.gather(*workers)

                task = await self._reload_task(session, task.id)
                if not task:
                    return

                if task.status == StructuredValidationTaskStatus.CANCELLED:
                    task.success = False
                    task.completed_at = task.completed_at or datetime.utcnow()
                    task.updated_at = datetime.utcnow()
                    session.add(task)
                    await session.commit()
                    return

                task.status = StructuredValidationTaskStatus.COMPLETED
                task.success = successful_items == total
                task.message = "Tarea completada" if task.success else "Tarea completada con incidencias"
                task.progress_percentage = 100
                task.progress_message = task.message
                task.completed_items = completed_items
                task.successful_items = successful_items
                task.failed_items = completed_items - successful_items
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                session.add(task)
                await session.commit()
                self._log_progress(task.id, task.message, level="success", progress_percentage=100)
            except Exception as exc:
                log.exception("Error ejecutando structured validation task %s", task_id)
                task.status = StructuredValidationTaskStatus.FAILED
                task.success = False
                task.error_message = str(exc)
                task.message = "La tarea fallo"
                task.progress_message = str(exc)
                task.updated_at = datetime.utcnow()
                task.completed_at = datetime.utcnow()
                session.add(task)
                await session.commit()
                self._log_progress(task.id, str(exc), level="error", progress_percentage=task.progress_percentage)


_structured_validation_task_service: StructuredValidationTaskService | None = None


def get_structured_validation_task_service() -> StructuredValidationTaskService:
    global _structured_validation_task_service
    if _structured_validation_task_service is None:
        _structured_validation_task_service = StructuredValidationTaskService()
    return _structured_validation_task_service
