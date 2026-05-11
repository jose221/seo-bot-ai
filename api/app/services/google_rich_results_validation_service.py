from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.handlers.seo_scrapper.google_rich_results_engine import (
    GoogleRichResultsEngine,
    InputType as GoogleInputType,
)
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisFinding,
    RichResultsAnalysisSummary,
    RichResultsScreenshot,
    RichResultsValidatorDetail,
)
from app.shared.rich_results_html_analyzer import (
    RichResultsHtmlFinding,
    analyze_rich_results_html,
    build_rich_results_findings_summary,
)
from app.services.browser_mode_registry_service import get_browser_mode_registry_service

logger = logging.getLogger(__name__)


class GoogleRichResultsValidationService:
    def __init__(self, proxy_url: Optional[str]) -> None:
        self.proxy_url = proxy_url

    def _build_engine(
        self,
        proxy_url: Optional[str] = None,
        browser_mode_code: Optional[str] = None,
    ) -> GoogleRichResultsEngine:
        effective_proxy = proxy_url if proxy_url is not None else self.proxy_url
        proxy_server = None
        if effective_proxy:
            parsed = urlparse(effective_proxy)
            proxy_server = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                proxy_server = f"{proxy_server}:{parsed.port}"
        browser_mode = get_browser_mode_registry_service().resolve_mode(browser_mode_code)

        return GoogleRichResultsEngine(
            proxy_server=proxy_server,
            screenshots_dir=f"{settings.STORAGE_PATH}/images",
            storage_url_prefix=f"{settings.STORAGE_URL_PREFIX.rstrip('/')}/images",
            headless=browser_mode.headless if browser_mode else False,
        )

    @staticmethod
    def _to_input_type(input_type: str) -> GoogleInputType:
        return GoogleInputType.HTML if input_type == "html" else GoogleInputType.URL

    @staticmethod
    def _build_findings_summary(
        findings: list[RichResultsAnalysisFinding],
    ) -> RichResultsAnalysisSummary:
        summary = build_rich_results_findings_summary(
            [RichResultsHtmlFinding(**item.model_dump()) for item in findings]
        )
        return RichResultsAnalysisSummary.model_validate(summary.to_dict())

    @staticmethod
    def _build_message(is_success: bool, blocked: bool, error_message: Optional[str]) -> str:
        if is_success:
            return "Reporte de Google Rich Results generado correctamente"
        if blocked:
            return "Google bloqueó la validación; se devuelven screenshots y el mensaje de error"
        return error_message or "No fue posible generar el reporte de Google Rich Results"

    async def validate(
        self,
        *,
        input_type: str,
        content: str,
        browser_mode_code: Optional[str] = None,
    ) -> RichResultsValidatorDetail:
        # Primer intento: sin proxy
        validation = await self._build_engine(proxy_url=None, browser_mode_code=browser_mode_code).validate(
            input_type=self._to_input_type(input_type),
            content=content,
        )

        # Si Google bloqueó, reintentar con el proxy configurado en .env
        if validation.blocked_by_google:
            fallback_proxy = settings.RICH_RESULTS_PROXY_URL.strip() if settings.RICH_RESULTS_PROXY_URL else None
            if fallback_proxy:
                logger.warning(
                    "Google bloqueó la solicitud sin proxy — reintentando con proxy de .env"
                )
                validation = await self._build_engine(
                    proxy_url=fallback_proxy,
                    browser_mode_code=browser_mode_code,
                ).validate(
                    input_type=self._to_input_type(input_type),
                    content=content,
                )

        findings = [
            RichResultsAnalysisFinding.model_validate(item.to_dict())
            for item in analyze_rich_results_html(validation.html_content or "")
        ]
        return RichResultsValidatorDetail(
            validator="google",
            label="Google Rich Results",
            enabled=True,
            executed=True,
            success=validation.is_success,
            method_used=validation.method_used,
            result_url=validation.result_url,
            message=self._build_message(
                validation.is_success,
                validation.blocked_by_google,
                validation.error_message,
            ),
            error_message=validation.error_message,
            blocked=validation.blocked_by_google,
            screenshots=[RichResultsScreenshot(**item) for item in validation.screenshots],
            findings=findings,
            findings_summary=self._build_findings_summary(findings),
            html_content=validation.html_content,
        )
