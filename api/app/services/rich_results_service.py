"""
Servicio orquestador para generar reportes de Google Rich Results y Schema.org.
"""
from __future__ import annotations

from typing import Optional

import trafilatura
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlmodel import select

from app.core.config import settings
from app.core.database import db_manager
from app.handlers.seo_scrapper.google_rich_results_engine import InputType
from app.models.webpage import WebPage
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisFinding,
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportRequest,
    RichResultsReportResponse,
    RichResultsValidatorDetail,
)
from app.services.ai_client import get_ai_client
from app.services.audit_engine import get_audit_engine
from app.services.google_rich_results_validation_service import GoogleRichResultsValidationService
from app.services.schema_org_validation_service import SchemaOrgValidationService


class RichResultsService:
    def __init__(self) -> None:
        self.ai_client = get_ai_client()

    def _resolve_proxy_url(self) -> Optional[str]:
        if settings.RICH_RESULTS_PROXY_URL and settings.RICH_RESULTS_PROXY_URL.strip():
            return settings.RICH_RESULTS_PROXY_URL.strip()
        return None

    @staticmethod
    def _build_disabled_segment(validator: str, label: str) -> RichResultsValidatorDetail:
        return RichResultsValidatorDetail(
            validator=validator,
            label=label,
            enabled=False,
            executed=False,
            message=f"Validación {label} desactivada para esta ejecución",
        )

    @staticmethod
    def _combine_findings(
        *segments: RichResultsValidatorDetail,
    ) -> list[RichResultsAnalysisFinding]:
        combined: list[RichResultsAnalysisFinding] = []
        for segment in segments:
            combined.extend(segment.findings)
        return combined

    def build_findings_summary(
        self,
        findings: list[RichResultsAnalysisFinding],
    ) -> RichResultsAnalysisSummary:
        by_severity: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for finding in findings:
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
            by_category[finding.category] = by_category.get(finding.category, 0) + 1
        return RichResultsAnalysisSummary(
            total=len(findings),
            by_severity=by_severity,
            by_category=by_category,
        )

    @staticmethod
    def _html_to_markdown(html_content: str) -> str:
        markdown = trafilatura.extract(
            html_content,
            output_format="markdown",
            include_links=True,
            include_images=False,
            include_tables=True,
        )
        if markdown:
            return markdown.strip()

        soup = BeautifulSoup(html_content, "lxml")
        return soup.get_text("\n", strip=True)

    @staticmethod
    def _combine_screenshots(*segments: RichResultsValidatorDetail) -> list:
        screenshots = []
        for segment in segments:
            screenshots.extend(segment.screenshots)
        return screenshots

    @staticmethod
    def _build_overall_success(*segments: RichResultsValidatorDetail) -> bool:
        executed = [segment for segment in segments if segment.enabled]
        return bool(executed) and all(segment.success for segment in executed)

    @staticmethod
    def _build_method_used(*segments: RichResultsValidatorDetail) -> str:
        methods = [segment.method_used for segment in segments if segment.enabled and segment.method_used]
        return ", ".join(dict.fromkeys(methods)) if methods else "none"

    @staticmethod
    def _build_result_url(
        google_validation: RichResultsValidatorDetail,
        schema_org_validation: RichResultsValidatorDetail,
    ) -> Optional[str]:
        return google_validation.result_url or schema_org_validation.result_url

    @staticmethod
    def _build_message(
        google_validation: RichResultsValidatorDetail,
        schema_org_validation: RichResultsValidatorDetail,
    ) -> str:
        messages = [
            f"{segment.label}: {segment.message}"
            for segment in (google_validation, schema_org_validation)
            if segment.enabled and segment.message
        ]
        return " | ".join(messages) if messages else "No fue posible generar el reporte"

    @staticmethod
    def _build_error_message(
        google_validation: RichResultsValidatorDetail,
        schema_org_validation: RichResultsValidatorDetail,
    ) -> Optional[str]:
        errors = [
            f"{segment.label}: {segment.error_message}"
            for segment in (google_validation, schema_org_validation)
            if segment.enabled and segment.error_message
        ]
        return " | ".join(errors) if errors else None

    async def _extract_html_from_url(self, url: str) -> str:
        target = None
        async with db_manager.async_session_context() as session:
            statement = select(WebPage).where(
                WebPage.url == url,
                WebPage.is_active == True,
            )
            target = (await session.execute(statement)).scalars().first()

        html_content: Optional[str] = None
        try:
            html_content = await get_audit_engine().fetch_html(url, timeout_ms=30_000)
        except Exception:
            html_content = None

        if not html_content and target and target.manual_html_content:
            html_content = target.manual_html_content

        if not html_content:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "No se pudo extraer el HTML para Rich Results."
                    + (
                        " El target no respondió al scraper y no hay HTML guardado."
                        if target
                        else " La URL no respondió al scraper."
                    )
                ),
            )

        return html_content

    async def _build_effective_input(
        self,
        payload: RichResultsReportRequest,
    ) -> tuple[InputType, str, Optional[str]]:
        if payload.is_url and payload.auto_extract_html:
            html_content = await self._extract_html_from_url(payload.content)
            return InputType.HTML, html_content, payload.content

        input_type = InputType.URL if payload.is_url else InputType.HTML
        return input_type, payload.content, payload.content if payload.is_url else None

    async def report_page(
        self,
        payload: RichResultsReportRequest,
        token: Optional[str] = None,
    ) -> RichResultsReportResponse:
        input_type, content, source_url = await self._build_effective_input(payload)
        proxy_url = self._resolve_proxy_url()
        google_service = GoogleRichResultsValidationService(proxy_url)
        schema_org_service = SchemaOrgValidationService(proxy_url)

        google_validation = (
            await google_service.validate(input_type=input_type.value, content=content or "")
            if payload.validate_google
            else self._build_disabled_segment("google", "Google Rich Results")
        )
        schema_org_validation = (
            await schema_org_service.validate(input_type=input_type.value, content=content or "")
            if payload.validate_schema_org
            else self._build_disabled_segment("schema_org", "Schema.org Validator")
        )

        google_markdown = self._html_to_markdown(google_validation.html_content or "") if google_validation.html_content else ""
        schema_markdown = self._html_to_markdown(schema_org_validation.html_content or "") if schema_org_validation.html_content else ""
        google_validation.markdown_content = google_markdown or None
        schema_org_validation.markdown_content = schema_markdown or None

        findings = self._combine_findings(google_validation, schema_org_validation)
        findings_summary = self.build_findings_summary(findings)
        ai_result: Optional[RichResultsAIResult] = None
        ai_error_message: Optional[str] = None

        combined_markdown_parts = []
        if google_markdown:
            combined_markdown_parts.append(f"## Google Rich Results\n\n{google_markdown}")
        if schema_markdown:
            combined_markdown_parts.append(f"## Schema.org Validator\n\n{schema_markdown}")
        combined_markdown = "\n\n".join(combined_markdown_parts).strip()

        if payload.get_ai_result and (google_validation.enabled or schema_org_validation.enabled):
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere un token válido para obtener get_ai_result"
                )

            if combined_markdown or findings:
                try:
                    ai_payload = await self.ai_client.analyze_rich_results_content(
                        markdown_content=combined_markdown,
                        rich_results_url=google_validation.result_url,
                        schema_org_url=schema_org_validation.result_url,
                        source_url=source_url,
                        findings=[item.model_dump() for item in findings],
                        findings_summary=findings_summary.model_dump(),
                        google_validation=google_validation.model_dump(),
                        schema_org_validation=schema_org_validation.model_dump(),
                        token=token
                    )
                    ai_result = RichResultsAIResult(**ai_payload)
                except HTTPException as exc:
                    ai_error_message = str(exc.detail)
            else:
                ai_error_message = "No hubo contenido utilizable para analizar con IA"

        return RichResultsReportResponse(
            success=self._build_overall_success(google_validation, schema_org_validation),
            input_type=input_type.value,
            method_used=self._build_method_used(google_validation, schema_org_validation),
            result_url=self._build_result_url(google_validation, schema_org_validation),
            message=self._build_message(google_validation, schema_org_validation),
            error_message=self._build_error_message(google_validation, schema_org_validation),
            blocked_by_google=google_validation.blocked,
            validate_google=payload.validate_google,
            validate_schema_org=payload.validate_schema_org,
            screenshots=self._combine_screenshots(google_validation, schema_org_validation),
            findings=findings,
            findings_summary=findings_summary,
            google_validation=google_validation,
            schema_org_validation=schema_org_validation,
            get_ai_result=ai_result,
            ai_error_message=ai_error_message
        )


_rich_results_service: Optional[RichResultsService] = None


def get_rich_results_service() -> RichResultsService:
    global _rich_results_service
    if _rich_results_service is None:
        _rich_results_service = RichResultsService()
    return _rich_results_service
