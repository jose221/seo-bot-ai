"""
Servicio para generar reportes de Google Rich Results.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

import trafilatura
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlmodel import select

from app.core.config import settings
from app.core.database import db_manager
from app.handlers.seo_scrapper.google_rich_results_engine import GoogleRichResultsEngine, InputType
from app.handlers.seo_scrapper.schema_org_validator import SchemaOrgValidatorEngine
from app.models.webpage import WebPage
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisFinding,
    RichResultsAnalysisSummary,
    RichResultsAIResult,
    RichResultsReportRequest,
    RichResultsReportResponse,
)
from app.services.schema_validators import SchemaOrgValidator
from app.shared.rich_results_html_analyzer import (
    RichResultsHtmlFinding,
    analyze_rich_results_html,
    build_rich_results_findings_summary,
)
from app.services.ai_client import get_ai_client
from app.services.audit_engine import get_audit_engine


class RichResultsService:
    def __init__(self) -> None:
        self.ai_client = get_ai_client()

    def _resolve_proxy_url(self) -> Optional[str]:
        if settings.RICH_RESULTS_PROXY_URL and settings.RICH_RESULTS_PROXY_URL.strip():
            return settings.RICH_RESULTS_PROXY_URL.strip()
        return None

    def _build_engine(self, proxy_url: Optional[str]) -> GoogleRichResultsEngine:
        proxy_server = None

        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_server = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                proxy_server = f"{proxy_server}:{parsed.port}"

        return GoogleRichResultsEngine(
            proxy_server=proxy_server,
            screenshots_dir=f"{settings.STORAGE_PATH}/images",
            storage_url_prefix=f"{settings.STORAGE_URL_PREFIX.rstrip('/')}/images"
        )

    def _build_engine_schema_validator(self, proxy_url: Optional[str]) -> SchemaOrgValidatorEngine:
      proxy_server = None

      if proxy_url:
        parsed = urlparse(proxy_url)
        proxy_server = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
          proxy_server = f"{proxy_server}:{parsed.port}"

      return SchemaOrgValidatorEngine(
        proxy_server=proxy_server,
        screenshots_dir=f"{settings.STORAGE_PATH}/images",
        storage_url_prefix=f"{settings.STORAGE_URL_PREFIX.rstrip('/')}/images"
      )

    def _html_to_markdown(self, html_content: str) -> str:
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

    def analyze_validation_html(self, html_content: str) -> list[RichResultsAnalysisFinding]:
        return [
            RichResultsAnalysisFinding.model_validate(item.to_dict())
            for item in analyze_rich_results_html(html_content)
        ]

    def build_findings_summary(
        self,
        findings: list[RichResultsAnalysisFinding],
    ) -> RichResultsAnalysisSummary:
        summary = build_rich_results_findings_summary(
            [
                RichResultsHtmlFinding(**finding.model_dump())
                for finding in findings
            ]
        )
        return RichResultsAnalysisSummary.model_validate(summary.to_dict())

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
        engine = self._build_engine(proxy_url)
        engine_schema_validator = self._build_engine_schema_validator(proxy_url)

        validation = await engine.validate(input_type=input_type, content=content or "")
        validation_schema = await engine_schema_validator.validate(input_type=input_type, content=content or "")
        findings = self.analyze_validation_html(validation.html_content or "")
        findings_summary = self.build_findings_summary(findings)
        ai_result: Optional[RichResultsAIResult] = None
        ai_error_message: Optional[str] = None

        if payload.get_ai_result and validation.is_success and validation.html_content and not validation.blocked_by_google:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere un token válido para obtener get_ai_result"
                )

            markdown_content = self._html_to_markdown(validation.html_content)
            if markdown_content or findings:
                try:
                    ai_payload = await self.ai_client.analyze_rich_results_content(
                        markdown_content=markdown_content,
                        rich_results_url=validation.result_url,
                        source_url=source_url,
                        findings=[item.model_dump() for item in findings],
                        findings_summary=findings_summary.model_dump(),
                        token=token
                    )
                    ai_result = RichResultsAIResult(**ai_payload)
                except HTTPException as exc:
                    ai_error_message = str(exc.detail)
            else:
                ai_error_message = "No hubo contenido utilizable para analizar con IA"

        if validation.is_success:
            message = "Reporte de Google Rich Results generado correctamente"
        elif validation.blocked_by_google:
            message = "Google bloqueó la validación; se devuelven screenshots y el mensaje de error"
        else:
            message = validation.error_message or "No fue posible generar el reporte de Google Rich Results"

        return RichResultsReportResponse(
            success=validation.is_success,
            input_type=input_type.value,
            method_used=validation.method_used,
            result_url=validation.result_url,
            message=message,
            error_message=validation.error_message,
            blocked_by_google=validation.blocked_by_google,
            screenshots=validation.screenshots,
            findings=findings,
            findings_summary=findings_summary,
            get_ai_result=ai_result,
            ai_error_message=ai_error_message
        )


_rich_results_service: Optional[RichResultsService] = None


def get_rich_results_service() -> RichResultsService:
    global _rich_results_service
    if _rich_results_service is None:
        _rich_results_service = RichResultsService()
    return _rich_results_service
