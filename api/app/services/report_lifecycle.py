import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import String, cast as sql_cast, desc
from sqlmodel import select

from app.core.config import settings
from app.core.database import db_manager
from app.models import (
    AuditComparison,
    AuditReport,
    AuditSchemaReview,
    AuditStatus,
    AuditUrlValidation,
    ComparisonStatus,
    SchemaAuditSourceType,
    SchemaAuditStatus,
    UrlValidationSourceType,
    UrlValidationStatus,
)
from app.services.audit_comparator import get_audit_comparator
from app.services.report_generator import ReportGenerator
from app.services.url_validation_service import get_url_validation_service

log = logging.getLogger(__name__)


class ReportLifecycleService:
    REPORT_TTL = timedelta(hours=24)
    CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
    REPORT_EXTENSIONS = {".pdf", ".docx", ".xlsx"}
    REPORT_PATH_FIELDS = {
        AuditReport: ("report_pdf_path", "report_word_path", "report_excel_path"),
        AuditComparison: (
            "report_pdf_path",
            "report_word_path",
            "report_excel_path",
            "proposal_report_pdf_path",
            "proposal_report_word_path",
        ),
        AuditSchemaReview: ("report_pdf_path", "report_word_path"),
        AuditUrlValidation: (
            "report_pdf_path",
            "report_word_path",
            "global_report_pdf_path",
            "global_report_word_path",
        ),
    }

    def __init__(self) -> None:
        self.reports_root = Path(settings.STORAGE_PATH) / "reports"

    async def ensure_audit_pdf(self, session, audit: AuditReport) -> str:
        current_path = self._consume_existing_path(audit, "report_pdf_path")
        if current_path:
            return current_path

        self._assert_completed(audit.status, "La auditoría aún no ha finalizado")
        self._assert_has_source_data(
            bool(audit.lighthouse_data or audit.seo_analysis or audit.ai_suggestions),
            "La auditoría no tiene datos suficientes para generar el PDF",
        )

        report_paths = ReportGenerator(audit=audit).generate_documents()
        self._replace_paths(
            audit,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, audit)
        return audit.report_pdf_path

    async def ensure_audit_word(self, session, audit: AuditReport) -> str:
        current_path = self._consume_existing_path(audit, "report_word_path")
        if current_path:
            return current_path

        self._assert_completed(audit.status, "La auditoría aún no ha finalizado")
        self._assert_has_source_data(
            bool(audit.lighthouse_data or audit.seo_analysis or audit.ai_suggestions),
            "La auditoría no tiene datos suficientes para generar el Word",
        )

        report_paths = ReportGenerator(audit=audit).generate_documents()
        self._replace_paths(
            audit,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, audit)
        return audit.report_word_path

    async def ensure_comparison_pdf(self, session, comparison: AuditComparison) -> str:
        current_path = self._consume_existing_path(comparison, "report_pdf_path")
        if current_path:
            return current_path

        self._assert_completed(comparison.status, "La comparación aún no ha finalizado")
        self._assert_has_source_data(
            bool(comparison.comparison_result),
            "La comparación no tiene datos suficientes para generar el PDF",
        )

        base_audit = await self._get_report_audit_for_comparison_async(session, comparison)
        self._assert_has_source_data(
            base_audit is not None,
            "No se encontró una auditoría base para generar el PDF de comparación",
        )

        report_paths = ReportGenerator(audit=base_audit).generate_comparison_documents(
            comparison.comparison_result
        )
        self._replace_paths(
            comparison,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, comparison)
        return comparison.report_pdf_path

    async def ensure_comparison_word(self, session, comparison: AuditComparison) -> str:
        current_path = self._consume_existing_path(comparison, "report_word_path")
        if current_path:
            return current_path

        self._assert_completed(comparison.status, "La comparación aún no ha finalizado")
        self._assert_has_source_data(
            bool(comparison.comparison_result),
            "La comparación no tiene datos suficientes para generar el Word",
        )

        base_audit = await self._get_report_audit_for_comparison_async(session, comparison)
        self._assert_has_source_data(
            base_audit is not None,
            "No se encontró una auditoría base para generar el Word de comparación",
        )

        report_paths = ReportGenerator(audit=base_audit).generate_comparison_documents(
            comparison.comparison_result
        )
        self._replace_paths(
            comparison,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, comparison)
        return comparison.report_word_path

    async def ensure_schema_pdf(self, session, schema_audit: AuditSchemaReview) -> str:
        current_path = self._consume_existing_path(schema_audit, "report_pdf_path")
        if current_path:
            return current_path

        report_audit, report_body = await self._build_schema_report_context_async(session, schema_audit)
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(report_body)
        self._replace_paths(
            schema_audit,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, schema_audit)
        return schema_audit.report_pdf_path

    async def ensure_schema_word(self, session, schema_audit: AuditSchemaReview) -> str:
        current_path = self._consume_existing_path(schema_audit, "report_word_path")
        if current_path:
            return current_path

        report_audit, report_body = await self._build_schema_report_context_async(session, schema_audit)
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(report_body)
        self._replace_paths(
            schema_audit,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, schema_audit)
        return schema_audit.report_word_path

    async def ensure_comparison_proposal_pdf(
        self,
        session,
        comparison: AuditComparison,
        token: str,
    ) -> str:
        current_path = self._consume_existing_path(comparison, "proposal_report_pdf_path")
        if current_path:
            return current_path

        report_audit, detailed_content = await self._build_comparison_proposal_context_async(
            session,
            comparison,
            token,
        )
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(
            detailed_content
        )
        self._replace_paths(
            comparison,
            proposal_report_pdf_path=report_paths["pdf_path"],
            proposal_report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, comparison)
        return comparison.proposal_report_pdf_path

    async def ensure_comparison_proposal_word(
        self,
        session,
        comparison: AuditComparison,
        token: str,
    ) -> str:
        current_path = self._consume_existing_path(comparison, "proposal_report_word_path")
        if current_path:
            return current_path

        report_audit, detailed_content = await self._build_comparison_proposal_context_async(
            session,
            comparison,
            token,
        )
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(
            detailed_content
        )
        self._replace_paths(
            comparison,
            proposal_report_pdf_path=report_paths["pdf_path"],
            proposal_report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, comparison)
        return comparison.proposal_report_word_path

    async def ensure_url_validation_pdf(self, session, validation: AuditUrlValidation) -> str:
        current_path = self._consume_existing_path(validation, "report_pdf_path")
        if current_path:
            return current_path

        report_audit, markdown = await self._build_url_validation_report_context_async(session, validation)
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(markdown)
        self._replace_paths(
            validation,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, validation)
        return validation.report_pdf_path

    async def ensure_url_validation_word(self, session, validation: AuditUrlValidation) -> str:
        current_path = self._consume_existing_path(validation, "report_word_path")
        if current_path:
            return current_path

        report_audit, markdown = await self._build_url_validation_report_context_async(session, validation)
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(markdown)
        self._replace_paths(
            validation,
            report_pdf_path=report_paths["pdf_path"],
            report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, validation)
        return validation.report_word_path

    async def ensure_url_validation_global_pdf(self, session, validation: AuditUrlValidation) -> str:
        current_path = self._consume_existing_path(validation, "global_report_pdf_path")
        if current_path:
            return current_path

        report_audit, markdown = await self._build_url_validation_global_report_context_async(
            session,
            validation,
        )
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(markdown)
        self._replace_paths(
            validation,
            global_report_pdf_path=report_paths["pdf_path"],
            global_report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, validation)
        return validation.global_report_pdf_path

    async def ensure_url_validation_global_word(self, session, validation: AuditUrlValidation) -> str:
        current_path = self._consume_existing_path(validation, "global_report_word_path")
        if current_path:
            return current_path

        report_audit, markdown = await self._build_url_validation_global_report_context_async(
            session,
            validation,
        )
        report_paths = ReportGenerator(audit=report_audit).generate_detailed_proposal_reports(markdown)
        self._replace_paths(
            validation,
            global_report_pdf_path=report_paths["pdf_path"],
            global_report_word_path=report_paths["word_path"],
        )
        await self._persist_async(session, validation)
        return validation.global_report_word_path

    async def run_cleanup_loop(self) -> None:
        while True:
            try:
                self.cleanup_expired_reports()
            except Exception:
                log.exception("Error cleaning up expired report files")
            await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)

    def cleanup_expired_reports(self) -> dict[str, int]:
        stats = {
            "db_paths_cleared": 0,
            "referenced_files_deleted": 0,
            "orphan_files_deleted": 0,
        }
        referenced_files: set[str] = set()

        with db_manager.sync_session_context() as session:
            for model, attrs in self.REPORT_PATH_FIELDS.items():
                records = session.execute(select(model)).scalars().all()
                for record in records:
                    changed = False
                    for attr in attrs:
                        raw_path = getattr(record, attr)
                        if not raw_path:
                            continue

                        file_path = Path(raw_path)
                        normalized = self._normalize_path(file_path)
                        if file_path.exists() and not self._is_expired(file_path):
                            referenced_files.add(normalized)
                            continue

                        if file_path.exists():
                            self._delete_file(file_path)
                            stats["referenced_files_deleted"] += 1

                        setattr(record, attr, None)
                        stats["db_paths_cleared"] += 1
                        changed = True

                    if changed:
                        session.add(record)

        stats["orphan_files_deleted"] = self._delete_orphaned_files(referenced_files)
        return stats

    async def _build_schema_report_context_async(
        self,
        session,
        schema_audit: AuditSchemaReview,
    ) -> tuple[AuditReport, str]:
        self._assert_completed(schema_audit.status, "La auditoría de schemas aún no ha finalizado")

        ai_report_text = ""
        if isinstance(schema_audit.progress_report, dict):
            ai_report_text = schema_audit.progress_report.get("ai_report", "") or ""

        report_body = "\n\n".join(
            [
                "# Auditoría de Schemas",
                ai_report_text or "Sin reporte IA de comparación.",
                "# Modelos de clases del esquema",
                schema_audit.cqrs_solid_model_text or "Sin modelos generados.",
            ]
        )

        report_audit = await self._get_report_audit_for_schema_async(session, schema_audit)
        self._assert_has_source_data(
            report_audit is not None,
            "No se encontró una auditoría base para generar el reporte de schemas",
        )
        return report_audit, report_body

    async def _build_comparison_proposal_context_async(
        self,
        session,
        comparison: AuditComparison,
        token: str,
    ) -> tuple[AuditReport, str]:
        self._assert_completed(comparison.status, "La comparación aún no ha finalizado")
        self._assert_has_source_data(
            bool(comparison.comparison_result),
            "La comparación no tiene datos suficientes para generar la propuesta detallada",
        )
        ai_schema_comparison = ""
        if isinstance(comparison.comparison_result, dict):
            ai_schema_comparison = comparison.comparison_result.get("ai_schema_comparison", "") or ""

        self._assert_has_source_data(
            len(ai_schema_comparison.strip()) > 0,
            "La comparación no tiene propuesta de schemas para generar el reporte detallado",
        )
        self._assert_has_source_data(
            bool(token),
            "No se encontró el token del usuario para regenerar el reporte detallado",
        )

        report_audit = await self._get_report_audit_for_comparison_async(session, comparison)
        self._assert_has_source_data(
            report_audit is not None,
            "No se encontró una auditoría base para generar la propuesta detallada",
        )

        detailed_response = await get_audit_comparator().generate_ai_detailed_proposal_report(
            schema_proposal=ai_schema_comparison,
            documentation_context=comparison.documentation_context,
            token=token,
        )
        detailed_content = detailed_response.get("content", "") or ""
        self._assert_has_source_data(
            bool(detailed_content.strip()),
            "No fue posible generar el contenido detallado de la propuesta",
        )
        return report_audit, detailed_content

    async def _build_url_validation_report_context_async(
        self,
        session,
        validation: AuditUrlValidation,
    ) -> tuple[AuditReport, str]:
        self._assert_completed(validation.status, "La validación de URLs aún no ha finalizado")
        results = validation.results_json if isinstance(validation.results_json, list) else []
        self._assert_has_source_data(
            bool(results),
            "La validación de URLs no tiene resultados para generar el reporte",
        )

        markdown = get_url_validation_service().build_consolidated_markdown(
            results=results,
            name_validation=validation.name_validation,
            description_validation=validation.description_validation,
            global_severity=validation.global_severity or "warning",
        )
        report_audit = await self._get_report_audit_for_url_validation_async(session, validation)
        self._assert_has_source_data(
            report_audit is not None,
            "No se encontró una auditoría base para generar el reporte de validación",
        )
        return report_audit, markdown

    async def _build_url_validation_global_report_context_async(
        self,
        session,
        validation: AuditUrlValidation,
    ) -> tuple[AuditReport, str]:
        self._assert_completed(validation.status, "La validación de URLs aún no ha finalizado")
        results = validation.results_json if isinstance(validation.results_json, list) else []
        self._assert_has_source_data(
            bool(results),
            "La validación de URLs no tiene resultados para generar el reporte global",
        )

        markdown = get_url_validation_service().build_global_report_markdown(
            ai_global_text=validation.global_report_ai_text or "",
            results=results,
            name_validation=validation.name_validation,
            description_validation=validation.description_validation,
            global_severity=validation.global_severity or "warning",
        )
        report_audit = await self._get_report_audit_for_url_validation_async(session, validation)
        self._assert_has_source_data(
            report_audit is not None,
            "No se encontró una auditoría base para generar el reporte global de validación",
        )
        return report_audit, markdown

    async def _get_report_audit_for_comparison_async(
        self,
        session,
        comparison: AuditComparison,
    ) -> Optional[AuditReport]:
        statement = (
            select(AuditReport)
            .where(
                AuditReport.web_page_id == comparison.base_web_page_id,
                sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value,
            )
            .order_by(desc(AuditReport.created_at))
            .limit(1)
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def _get_report_audit_for_schema_async(
        self,
        session,
        schema_audit: AuditSchemaReview,
    ) -> Optional[AuditReport]:
        if schema_audit.source_type == SchemaAuditSourceType.AUDIT_PAGE:
            return await session.get(AuditReport, schema_audit.source_id)

        comparison = await session.get(AuditComparison, schema_audit.source_id)
        if not comparison:
            return None
        return await self._get_report_audit_for_comparison_async(session, comparison)

    async def _get_report_audit_for_url_validation_async(
        self,
        session,
        validation: AuditUrlValidation,
    ) -> Optional[AuditReport]:
        if validation.source_type == UrlValidationSourceType.AUDIT_PAGE:
            return await session.get(AuditReport, validation.source_id)

        comparison = await session.get(AuditComparison, validation.source_id)
        if not comparison:
            return None
        return await self._get_report_audit_for_comparison_async(session, comparison)

    @staticmethod
    async def _persist_async(session, entity: Any) -> None:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)

    def _consume_existing_path(self, entity: Any, attr_name: str) -> Optional[str]:
        raw_path = getattr(entity, attr_name, None)
        if not raw_path:
            return None

        file_path = Path(raw_path)
        if not file_path.exists():
            setattr(entity, attr_name, None)
            return None

        if self._is_expired(file_path):
            self._delete_file(file_path)
            setattr(entity, attr_name, None)
            return None

        return str(file_path)

    def _replace_paths(self, entity: Any, **new_paths: Optional[str]) -> None:
        for attr_name, new_path in new_paths.items():
            current_path = getattr(entity, attr_name, None)
            if current_path and current_path != new_path:
                self._delete_file(Path(current_path))
            setattr(entity, attr_name, new_path)

    @classmethod
    def _assert_completed(cls, status_value: Any, message: str) -> None:
        if status_value not in {
            AuditStatus.COMPLETED,
            ComparisonStatus.COMPLETED,
            SchemaAuditStatus.COMPLETED,
            UrlValidationStatus.COMPLETED,
            AuditStatus.COMPLETED.value,
            ComparisonStatus.COMPLETED.value,
            SchemaAuditStatus.COMPLETED.value,
            UrlValidationStatus.COMPLETED.value,
        }:
            raise ValueError(message)

    @staticmethod
    def _assert_has_source_data(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    @classmethod
    def _is_expired(cls, file_path: Path) -> bool:
        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        return datetime.now(timezone.utc) - modified_at >= cls.REPORT_TTL

    @staticmethod
    def _delete_file(file_path: Path) -> None:
        try:
            if file_path.exists():
                file_path.unlink()
        except FileNotFoundError:
            return
        except OSError:
            log.exception("No se pudo eliminar el archivo de reporte: %s", file_path)

    def _delete_orphaned_files(self, referenced_files: set[str]) -> int:
        if not self.reports_root.exists():
            return 0

        deleted = 0
        for file_path in self.reports_root.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in self.REPORT_EXTENSIONS:
                continue

            normalized = self._normalize_path(file_path)
            if normalized in referenced_files or not self._is_expired(file_path):
                continue

            self._delete_file(file_path)
            deleted += 1

        return deleted

    @staticmethod
    def _normalize_path(file_path: Path) -> str:
        try:
            return str(file_path.resolve())
        except OSError:
            return str(file_path)


_report_lifecycle_service: Optional[ReportLifecycleService] = None


def get_report_lifecycle_service() -> ReportLifecycleService:
    global _report_lifecycle_service
    if _report_lifecycle_service is None:
        _report_lifecycle_service = ReportLifecycleService()
    return _report_lifecycle_service
