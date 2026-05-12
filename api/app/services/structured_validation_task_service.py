from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import load_only
from sqlmodel import desc, select

from app.core.database import db_manager
from app.models.rich_results_report import RichResultsReport
from app.models.structured_validation_task import (
    StructuredValidationInputMode,
    StructuredValidationTask,
    StructuredValidationTaskStatus,
)
from app.services.browser_mode_registry_service import get_browser_mode_registry_service
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsValidatorDetail,
)
from app.schemas.structured_validation_schemas import (
    StructuredValidationBrowserModeOption,
    StructuredValidationCreateRequest,
    StructuredValidationTaskItem,
    StructuredValidationTaskItemsSummary,
    StructuredValidationTaskListItem,
    StructuredValidationTaskListResponse,
    StructuredValidationTaskResponse,
)
from app.services.rich_results_report_service import get_rich_results_report_service
from app.services.rich_results_service import get_rich_results_service
from app.services.task_notification_service import get_task_notification_service
from app.services.task_progress_service import get_task_progress_service

log = logging.getLogger(__name__)


class StructuredValidationTaskService:
    GOOGLE_VALIDATOR_URL = "https://search.google.com/test/rich-results?hl=es"
    SCHEMA_VALIDATOR_URL = "https://validator.schema.org/"
    TASK_TYPE = "structured_validation_task"
    BATCH_CONCURRENCY = 7
    BATCH_STAGGER_MIN_SECONDS = 5
    BATCH_STAGGER_MAX_SECONDS = 30
    CONTROL_POLL_SECONDS = 1.0
    DEFAULT_DETAIL_PAGE_SIZE = 10
    MAX_DETAIL_PAGE_SIZE = 10000
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
    def _compact_validator_payload(cls, raw_validator: Any) -> Dict[str, Any]:
        if isinstance(raw_validator, RichResultsValidatorDetail):
            payload = raw_validator.model_dump(mode="json")
        elif isinstance(raw_validator, dict):
            payload = dict(raw_validator)
        else:
            return {}

        payload.pop("html_content", None)
        payload.pop("markdown_content", None)
        return payload

    @classmethod
    def _compact_report_payload(cls, raw_report: Any) -> Dict[str, Any]:
        if isinstance(raw_report, RichResultsReportResponse):
            payload = raw_report.model_dump(mode="json")
        elif isinstance(raw_report, dict):
            payload = dict(raw_report)
        else:
            return {}

        compact_payload: Dict[str, Any] = {
            "success": bool(payload.get("success")),
            "input_type": payload.get("input_type", StructuredValidationInputMode.URL.value),
            "method_used": payload.get("method_used", "unknown"),
            "message": payload.get("message") or "",
            "blocked_by_google": bool(payload.get("blocked_by_google", False)),
            "validate_google": bool(payload.get("validate_google", True)),
            "validate_schema_org": bool(payload.get("validate_schema_org", True)),
            "saved": bool(payload.get("saved", False)),
        }

        for field_name in ("result_url", "error_message", "get_ai_result", "ai_error_message", "report_id"):
            if field_name in payload:
                compact_payload[field_name] = payload.get(field_name)

        google_validation = cls._compact_validator_payload(payload.get("google_validation"))
        if google_validation:
            compact_payload["google_validation"] = google_validation

        schema_org_validation = cls._compact_validator_payload(payload.get("schema_org_validation"))
        if schema_org_validation:
            compact_payload["schema_org_validation"] = schema_org_validation

        return compact_payload

    @classmethod
    def _compact_serialized_item(cls, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        compact_item = dict(raw_item)
        report_payload = raw_item.get("report")
        if isinstance(report_payload, dict) or isinstance(report_payload, RichResultsReportResponse):
            compact_item["report"] = cls._compact_report_payload(report_payload)
        return compact_item

    @classmethod
    def _normalize_detail_pagination(cls, *, page: int, page_size: int) -> tuple[int, int]:
        normalized_page = max(1, int(page))
        normalized_page_size = max(1, min(cls.MAX_DETAIL_PAGE_SIZE, int(page_size)))
        return normalized_page, normalized_page_size

    @staticmethod
    def _slice_items(items: List[Any], *, page: int, page_size: int) -> List[Any]:
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end]

    @classmethod
    def _build_task_items_summary(
        cls,
        *,
        total_items: int,
        completed_items: int,
        raw_results: List[Dict[str, Any]],
    ) -> StructuredValidationTaskItemsSummary:
        counts = {
            "ok": 0,
            "warning": 0,
            "critical": 0,
            "error": 0,
        }
        processed_items = 0

        for raw_item in raw_results:
            if not isinstance(raw_item, dict):
                continue
            processed_items += 1
            severity = raw_item.get("severity")
            if severity in counts:
                counts[severity] += 1
            elif raw_item.get("success"):
                counts["ok"] += 1

        pending_items = max(total_items - max(completed_items, processed_items), 0)
        return StructuredValidationTaskItemsSummary(
            total=total_items,
            ok=counts["ok"],
            warning=counts["warning"],
            critical=counts["critical"],
            error=counts["error"],
            pending=pending_items,
        )

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
            "report": cls._compact_report_payload(report),
        }

    @classmethod
    def _deserialize_item(cls, raw: Dict[str, Any]) -> StructuredValidationTaskItem:
        compact_raw = cls._compact_serialized_item(raw)
        report_payload = compact_raw.get("report") or {}
        return StructuredValidationTaskItem(
            item_key=compact_raw.get("item_key", ""),
            input_type=StructuredValidationInputMode(
                compact_raw.get("input_type", StructuredValidationInputMode.URL.value)
            ),
            label=compact_raw.get("label", ""),
            source_preview=compact_raw.get("source_preview"),
            source_value=compact_raw.get("source_value"),
            success=bool(compact_raw.get("success")),
            severity=compact_raw.get("severity"),
            message=compact_raw.get("message"),
            error_message=compact_raw.get("error_message"),
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
            result_url=StructuredValidationTaskService.GOOGLE_VALIDATOR_URL if validate_google else StructuredValidationTaskService.SCHEMA_VALIDATOR_URL if validate_schema_org else None,
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
                result_url=StructuredValidationTaskService.GOOGLE_VALIDATOR_URL if validate_google else None,
                error_message=message if validate_google else None,
            ),
            schema_org_validation=RichResultsValidatorDetail(
                validator="schema_org",
                label="Schema.org Validator",
                enabled=validate_schema_org,
                executed=False,
                result_url=StructuredValidationTaskService.SCHEMA_VALIDATOR_URL if validate_schema_org else None,
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
        full_report = RichResultsReportResponse(
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
        return RichResultsReportResponse.model_validate(self._compact_report_payload(full_report))

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

    def _build_legacy_task_response(
        self,
        report: RichResultsReport,
        *,
        page: int = 1,
        page_size: int = DEFAULT_DETAIL_PAGE_SIZE,
    ) -> StructuredValidationTaskResponse:
        page, page_size = self._normalize_detail_pagination(page=page, page_size=page_size)
        embedded_report = self._build_embedded_legacy_report(report)
        report_status = str(report.status)
        is_pending = report_status in {"pending", "in_progress"}
        is_finished = report_status in {"completed", "failed"}
        item = StructuredValidationTaskItem(
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
        paged_items = self._slice_items([item], page=page, page_size=page_size)
        return StructuredValidationTaskResponse(
            id=report.id,
            task_kind=self._legacy_task_kind(),
            supports_runtime_control=False,
            input_mode=StructuredValidationInputMode.URL,
            name=report.url,
            description=report.message,
            ai_instruction=None,
            browser_mode_code=None,
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
            page=page,
            page_size=page_size,
            summary=StructuredValidationTaskItemsSummary(
                total=1,
                ok=1 if report.success else 0,
                warning=0,
                critical=0 if report.success else 1,
                error=0,
                pending=1 if is_pending else 0,
            ),
            items=paged_items,
        )

    @staticmethod
    def _build_task_route(task_id: UUID) -> str:
        return f"/admin/audit/structured-validations/{task_id}/info"

    @staticmethod
    def _build_list_item_payload(task: StructuredValidationTask) -> dict[str, Any]:
        return StructuredValidationTaskListItem(
            id=task.id,
            task_kind=StructuredValidationTaskService.TASK_TYPE,
            supports_runtime_control=True,
            input_mode=task.input_mode,
            name=task.name,
            description=task.description,
            status=task.status,
            progress_percentage=task.progress_percentage,
            progress_message=task.progress_message,
            total_items=task.total_items,
            completed_items=task.completed_items,
            successful_items=task.successful_items,
            failed_items=task.failed_items,
            validate_google=task.validate_google,
            validate_schema_org=task.validate_schema_org,
            requested_ai_result=task.requested_ai_result,
            created_at=task.created_at,
            completed_at=task.completed_at,
        ).model_dump(mode="json")

    @classmethod
    def _build_detail_payload_from_task(
        cls,
        task: StructuredValidationTask,
        *,
        summary: StructuredValidationTaskItemsSummary | None = None,
    ) -> dict[str, Any]:
        resolved_summary = summary or cls._build_task_items_summary(
            total_items=task.total_items or len(task.inputs_json or []),
            completed_items=task.completed_items,
            raw_results=list(task.results_json or []),
        )
        return {
            "id": str(task.id),
            "status": task.status.value if isinstance(task.status, StructuredValidationTaskStatus) else str(task.status),
            "progress_percentage": task.progress_percentage,
            "progress_message": task.progress_message,
            "total_items": task.total_items,
            "completed_items": task.completed_items,
            "successful_items": task.successful_items,
            "failed_items": task.failed_items,
            "success": task.success,
            "message": task.message,
            "error_message": task.error_message,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "summary": resolved_summary.model_dump(mode="json"),
        }

    @classmethod
    def _build_item_update_payload(
        cls,
        *,
        item_key: str,
        input_index: int,
        item_payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "item_key": item_key,
            "input_index": input_index,
            "item": cls._deserialize_item(item_payload).model_dump(mode="json"),
        }

    async def _publish_task_change(
        self,
        *,
        task: StructuredValidationTask,
        action: str,
        summary: StructuredValidationTaskItemsSummary | None = None,
        item_update: dict[str, Any] | None = None,
    ) -> None:
        await get_task_notification_service().publish_structured_validation_task_change(
            user_id=task.user_id,
            action=action,
            task_id=task.id,
            route=self._build_task_route(task.id),
            list_item=self._build_list_item_payload(task),
            detail=self._build_detail_payload_from_task(task, summary=summary),
            item_update=item_update,
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

    async def _load_runtime_task(self, task_id: UUID) -> Optional[StructuredValidationTask]:
        async with db_manager.async_session_context() as session:
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

    async def _sleep_with_runtime_control(self, task_id: UUID, delay_seconds: float) -> Optional[StructuredValidationTaskStatus]:
        remaining = max(0.0, float(delay_seconds))
        while remaining > 0:
            status = await self._wait_until_resumable(task_id)
            if status is None or status == StructuredValidationTaskStatus.CANCELLED:
                return status

            sleep_slice = min(self.CONTROL_POLL_SECONDS, remaining)
            await asyncio.sleep(sleep_slice)
            remaining -= sleep_slice

        return await self._get_runtime_status(task_id)

    async def _persist_runtime_progress(
        self,
        *,
        task_id: UUID,
        inputs_json: list[dict[str, Any]],
        results_by_key: Dict[str, Dict[str, Any]],
        completed_items: int,
        successful_items: int,
        total: int,
        progress_value: int,
        item_update: dict[str, Any] | None = None,
    ) -> Optional[StructuredValidationTask]:
        async with db_manager.async_session_context() as session:
            task = await self.get_task(session, task_id=task_id)
            if not task:
                return None

            ordered_results = [
                results_by_key[item.get("item_key") or item.get("label") or ""]
                for item in inputs_json
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
            await session.refresh(task)
            await self._publish_task_change(
                task=task,
                action="progress",
                summary=self._build_task_items_summary(
                    total_items=task.total_items or len(inputs_json),
                    completed_items=task.completed_items,
                    raw_results=ordered_results,
                ),
                item_update=item_update,
            )
            return task

    async def _mark_runtime_task_started(self, task_id: UUID) -> Optional[StructuredValidationTask]:
        async with db_manager.async_session_context() as session:
            task = await self.get_task(session, task_id=task_id)
            if not task:
                return None

            if task.status == StructuredValidationTaskStatus.PENDING:
                task.status = StructuredValidationTaskStatus.IN_PROGRESS
                task.progress_percentage = max(task.progress_percentage, 5)
                task.message = "Tarea en progreso"
                task.progress_message = "Iniciando validaciones"
                task.updated_at = datetime.utcnow()
                task.completed_at = None
                session.add(task)
                await session.commit()
                await session.refresh(task)
                await self._publish_task_change(task=task, action="status")
            return task

    async def _mark_runtime_task_completed(
        self,
        *,
        task_id: UUID,
        completed_items: int,
        successful_items: int,
        total: int,
    ) -> Optional[StructuredValidationTask]:
        async with db_manager.async_session_context() as session:
            task = await self.get_task(session, task_id=task_id)
            if not task:
                return None

            if task.status == StructuredValidationTaskStatus.CANCELLED:
                task.success = False
                task.completed_at = task.completed_at or datetime.utcnow()
                task.updated_at = datetime.utcnow()
            else:
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
            await session.refresh(task)
            await self._publish_task_change(task=task, action="completed")
            return task

    async def _mark_runtime_task_failed(
        self,
        *,
        task_id: UUID,
        error_message: str,
        progress_percentage: int,
    ) -> Optional[StructuredValidationTask]:
        async with db_manager.async_session_context() as session:
            task = await self.get_task(session, task_id=task_id)
            if not task:
                return None

            task.status = StructuredValidationTaskStatus.FAILED
            task.success = False
            task.error_message = error_message
            task.message = "La tarea fallo"
            task.progress_message = error_message
            task.progress_percentage = progress_percentage
            task.updated_at = datetime.utcnow()
            task.completed_at = datetime.utcnow()
            session.add(task)
            await session.commit()
            await session.refresh(task)
            await self._publish_task_change(task=task, action="failed")
            return task

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
        await self._publish_task_change(task=task, action="status")
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
        await self._publish_task_change(task=task, action="status")
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
        await self._publish_task_change(task=task, action="status")
        return task

    async def create_task(
        self,
        session,
        *,
        user_id: UUID,
        payload: StructuredValidationCreateRequest,
    ) -> StructuredValidationTask:
        get_browser_mode_registry_service().resolve_mode(payload.browser_mode_code)
        inputs = self._build_inputs(payload)
        task = StructuredValidationTask(
            user_id=user_id,
            input_mode=payload.input_mode,
            name=payload.name,
            description=payload.description,
            ai_instruction=payload.ai_instruction,
            browser_mode_code=payload.browser_mode_code,
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
        await self._publish_task_change(task=task, action="created")
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
        await self._publish_task_change(task=task, action="status")
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
                .options(load_only(
                    StructuredValidationTask.id,
                    StructuredValidationTask.user_id,
                    StructuredValidationTask.input_mode,
                    StructuredValidationTask.name,
                    StructuredValidationTask.description,
                    StructuredValidationTask.browser_mode_code,
                    StructuredValidationTask.status,
                    StructuredValidationTask.progress_percentage,
                    StructuredValidationTask.progress_message,
                    StructuredValidationTask.total_items,
                    StructuredValidationTask.completed_items,
                    StructuredValidationTask.successful_items,
                    StructuredValidationTask.failed_items,
                    StructuredValidationTask.validate_google,
                    StructuredValidationTask.validate_schema_org,
                    StructuredValidationTask.requested_ai_result,
                    StructuredValidationTask.created_at,
                    StructuredValidationTask.completed_at,
                ))
                .where(StructuredValidationTask.user_id == user_id)
                .order_by(desc(StructuredValidationTask.created_at))
                .limit(fetch_limit)
            )
        ).scalars().all()
        legacy_reports = (
            await session.execute(
                select(RichResultsReport)
                .options(load_only(
                    RichResultsReport.id,
                    RichResultsReport.user_id,
                    RichResultsReport.url,
                    RichResultsReport.status,
                    RichResultsReport.progress_percentage,
                    RichResultsReport.progress_message,
                    RichResultsReport.success,
                    RichResultsReport.message,
                    RichResultsReport.validate_google,
                    RichResultsReport.validate_schema_org,
                    RichResultsReport.requested_ai_result,
                    RichResultsReport.created_at,
                ))
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

    def build_task_response(
        self,
        task: StructuredValidationTask,
        *,
        page: int = 1,
        page_size: int = DEFAULT_DETAIL_PAGE_SIZE,
    ) -> StructuredValidationTaskResponse:
        page, page_size = self._normalize_detail_pagination(page=page, page_size=page_size)
        all_inputs = list(task.inputs_json or [])
        total_items = task.total_items or len(all_inputs)
        page_inputs = self._slice_items(all_inputs, page=page, page_size=page_size)
        page_item_keys = {
            (item.get("item_key") or item.get("label") or "")
            for item in page_inputs
            if item.get("item_key") or item.get("label")
        }
        completed_items_by_key = {
            item.get("item_key", ""): self._deserialize_item(item)
            for item in (task.results_json or [])
            if item.get("item_key") and item.get("item_key") in page_item_keys
        }
        ordered_items: List[StructuredValidationTaskItem] = []
        for raw_input in page_inputs:
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
            browser_mode_code=task.browser_mode_code,
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
            page=page,
            page_size=page_size,
            summary=self._build_task_items_summary(
                total_items=total_items,
                completed_items=task.completed_items,
                raw_results=list(task.results_json or []),
            ),
            items=ordered_items,
        )

    def build_legacy_response(
        self,
        report: RichResultsReport,
        *,
        page: int = 1,
        page_size: int = DEFAULT_DETAIL_PAGE_SIZE,
    ) -> StructuredValidationTaskResponse:
        return self._build_legacy_task_response(report, page=page, page_size=page_size)

    def list_available_browser_modes(self) -> list[StructuredValidationBrowserModeOption]:
        return [
            StructuredValidationBrowserModeOption(
                code=mode.code,
                name=mode.name,
                description=mode.description,
                available_web=mode.available_web,
            )
            for mode in get_browser_mode_registry_service().list_available_modes()
        ]

    async def delete_task(self, session, *, task: StructuredValidationTask) -> None:
        await session.delete(task)
        await session.commit()

    async def run_task(self, *, task_id: UUID, token: str = "") -> None:
        task = await self._load_runtime_task(task_id)
        if not task:
            return

        try:
            if task.status == StructuredValidationTaskStatus.CANCELLED:
                return

            started_task = await self._mark_runtime_task_started(task_id)
            if not started_task:
                return
            task = started_task
            if task.status == StructuredValidationTaskStatus.IN_PROGRESS:
                self._log_progress(task.id, "Iniciando validacion de elementos", progress_percentage=task.progress_percentage)

            total = max(1, len(task.inputs_json or []))
            task_inputs = list(task.inputs_json or [])
            validate_google = task.validate_google
            validate_schema_org = task.validate_schema_org
            requested_ai_result = task.requested_ai_result
            auto_extract_html = task.auto_extract_html
            browser_mode_code = task.browser_mode_code

            results_by_key: Dict[str, Dict[str, Any]] = {
                item.get("item_key", ""): self._compact_serialized_item(item)
                for item in (task.results_json or [])
                if item.get("item_key")
            }
            completed_items = len(results_by_key)
            successful_items = sum(1 for item in results_by_key.values() if item.get("success"))
            pending_inputs = [
                (index, item)
                for index, item in enumerate(task_inputs, start=1)
                if (item.get("item_key") or item.get("label") or "") not in results_by_key
            ]
            update_lock = asyncio.Lock()

            async def process_item(index: int, item: Dict[str, Any]) -> tuple[str, str, Dict[str, Any], bool]:
                input_type = StructuredValidationInputMode(
                    item.get("input_type", StructuredValidationInputMode.URL.value)
                )
                label = item.get("label") or item.get("item_key") or f"Elemento {index}"
                source_value = item.get("value") or ""
                item_key = item.get("item_key") or label

                self._log_progress(
                    task_id,
                    f"Procesando {label}",
                    progress_percentage=self._clamp_progress(int((max(completed_items, 0) / total) * 100)),
                )
                try:
                    report_payload = RichResultsReportRequest(
                        content=source_value,
                        is_url=input_type == StructuredValidationInputMode.URL,
                        get_ai_result=requested_ai_result,
                        auto_extract_html=auto_extract_html if input_type == StructuredValidationInputMode.URL else False,
                        validate_google=validate_google,
                        validate_schema_org=validate_schema_org,
                        browser_mode_code=browser_mode_code,
                    )
                    report = await get_rich_results_service().report_page(report_payload, token=token)
                except Exception as exc:
                    log.exception("Error procesando elemento %s de structured task %s", label, task_id)
                    report = self._build_failed_report(
                        input_type=input_type,
                        validate_google=validate_google,
                        validate_schema_org=validate_schema_org,
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

            async def process_scheduled_item(
                index: int,
                item: Dict[str, Any],
                *,
                launch_delay_seconds: float,
            ) -> None:
                nonlocal completed_items, successful_items
                runtime_status = await self._wait_until_resumable(task_id)
                if runtime_status is None or runtime_status == StructuredValidationTaskStatus.CANCELLED:
                    return

                if launch_delay_seconds > 0:
                    delayed_status = await self._sleep_with_runtime_control(task_id, launch_delay_seconds)
                    if delayed_status is None or delayed_status == StructuredValidationTaskStatus.CANCELLED:
                        return

                runtime_status = await self._wait_until_resumable(task_id)
                if runtime_status is None or runtime_status == StructuredValidationTaskStatus.CANCELLED:
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
                        task_id,
                        f"{label}: {report_message}",
                        level="success" if success else "warning",
                        progress_percentage=progress_value,
                    )

                    persisted_task = await self._persist_runtime_progress(
                        task_id=task_id,
                        inputs_json=task_inputs,
                        results_by_key=results_by_key,
                        completed_items=completed_items,
                        successful_items=successful_items,
                        total=total,
                        progress_value=progress_value,
                        item_update=self._build_item_update_payload(
                            item_key=item_key,
                            input_index=index,
                            item_payload=serialized,
                        ),
                    )
                    if not persisted_task or persisted_task.status == StructuredValidationTaskStatus.CANCELLED:
                        return

            def build_batches(items: list[tuple[int, Dict[str, Any]]]) -> list[list[tuple[int, Dict[str, Any]]]]:
                batch_size = max(1, self.BATCH_CONCURRENCY)
                return [items[offset:offset + batch_size] for offset in range(0, len(items), batch_size)]

            pending_batches = build_batches(pending_inputs)
            for batch_index, batch_items in enumerate(pending_batches, start=1):
                runtime_status = await self._wait_until_resumable(task_id)
                if runtime_status is None or runtime_status == StructuredValidationTaskStatus.CANCELLED:
                    break

                self._log_progress(
                    task_id,
                    f"Iniciando lote {batch_index} de {len(pending_batches)} con {len(batch_items)} elementos",
                    progress_percentage=self._clamp_progress(int((completed_items / total) * 100)),
                )

                cumulative_delay = 0.0
                scheduled_workers = []
                for item_position, (index, item) in enumerate(batch_items, start=1):
                    if item_position > 1:
                        cumulative_delay += random.uniform(
                            self.BATCH_STAGGER_MIN_SECONDS,
                            self.BATCH_STAGGER_MAX_SECONDS,
                        )

                    label = item.get("label") or item.get("item_key") or f"Elemento {index}"
                    if cumulative_delay > 0:
                        self._log_progress(
                            task_id,
                            f"{label}: programado para iniciar en {int(round(cumulative_delay))} segundos",
                            progress_percentage=self._clamp_progress(int((completed_items / total) * 100)),
                        )

                    scheduled_workers.append(
                        asyncio.create_task(
                            process_scheduled_item(
                                index,
                                item,
                                launch_delay_seconds=cumulative_delay,
                            )
                        )
                    )

                await asyncio.gather(*scheduled_workers)

                runtime_status = await self._get_runtime_status(task_id)
                if runtime_status is None or runtime_status == StructuredValidationTaskStatus.CANCELLED:
                    break

            final_task = await self._mark_runtime_task_completed(
                task_id=task_id,
                completed_items=completed_items,
                successful_items=successful_items,
                total=total,
            )
            if final_task and final_task.status == StructuredValidationTaskStatus.COMPLETED:
                self._log_progress(final_task.id, final_task.message, level="success", progress_percentage=100)
        except Exception as exc:
            log.exception("Error ejecutando structured validation task %s", task_id)
            progress_percentage = self._clamp_progress(int((completed_items / total) * 100)) if 'completed_items' in locals() and 'total' in locals() else 0
            failed_task = await self._mark_runtime_task_failed(
                task_id=task_id,
                error_message=str(exc),
                progress_percentage=progress_percentage,
            )
            self._log_progress(task_id, str(exc), level="error", progress_percentage=failed_task.progress_percentage if failed_task else progress_percentage)


_structured_validation_task_service: StructuredValidationTaskService | None = None


def get_structured_validation_task_service() -> StructuredValidationTaskService:
    global _structured_validation_task_service
    if _structured_validation_task_service is None:
        _structured_validation_task_service = StructuredValidationTaskService()
    return _structured_validation_task_service
