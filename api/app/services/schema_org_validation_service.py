from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.handlers.seo_scrapper.schema_org_validator import (
    InputType as SchemaInputType,
    SchemaOrgValidatorEngine,
)
from app.schemas.rich_results_schemas import (
    RichResultsAnalysisFinding,
    RichResultsAnalysisSummary,
    RichResultsScreenshot,
    RichResultsValidatorDetail,
)
from app.shared.schema_org_html_analyzer import (
    SchemaOrgHtmlFinding,
    analyze_schema_org_html,
    build_schema_org_findings_summary,
)
from app.shared.schema_org_local_validator import validate_locally

logger = logging.getLogger(__name__)


class SchemaOrgValidationService:
    def __init__(self, proxy_url: Optional[str]) -> None:
        self.proxy_url = proxy_url

    def _build_engine(self, proxy_url: Optional[str] = None) -> SchemaOrgValidatorEngine:
        effective_proxy = proxy_url if proxy_url is not None else self.proxy_url
        proxy_server = None
        if effective_proxy:
            parsed = urlparse(effective_proxy)
            proxy_server = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                proxy_server = f"{proxy_server}:{parsed.port}"

        return SchemaOrgValidatorEngine(
            proxy_server=proxy_server,
            screenshots_dir=f"{settings.STORAGE_PATH}/images/schema_org",
            storage_url_prefix=f"{settings.STORAGE_URL_PREFIX.rstrip('/')}/images/schema_org",
        )

    @staticmethod
    def _to_input_type(input_type: str) -> SchemaInputType:
        return SchemaInputType.HTML if input_type == "html" else SchemaInputType.URL

    @staticmethod
    def _build_findings_summary(
        findings: list[RichResultsAnalysisFinding],
    ) -> RichResultsAnalysisSummary:
        summary = build_schema_org_findings_summary(
            [SchemaOrgHtmlFinding(**item.model_dump()) for item in findings]
        )
        return RichResultsAnalysisSummary.model_validate(summary.to_dict())

    @staticmethod
    def _build_message(is_success: bool, error_message: Optional[str]) -> str:
        if is_success:
            return "Reporte de Schema.org Validator generado correctamente"
        return error_message or "No fue posible generar el reporte de Schema.org Validator"

    async def validate(self, *, input_type: str, content: str) -> RichResultsValidatorDetail:
        # Primer intento: sin proxy
        validation = await self._build_engine(proxy_url=None).validate(
            input_type=self._to_input_type(input_type),
            content=content,
        )

        # Si bloqueó, reintentar con el proxy configurado en .env antes del fallback local
        if validation.blocked_by_schema:
            fallback_proxy = settings.RICH_RESULTS_PROXY_URL.strip() if settings.RICH_RESULTS_PROXY_URL else None
            if fallback_proxy:
                logger.warning(
                    "validator.schema.org bloqueó sin proxy — reintentando con proxy de .env"
                )
                validation = await self._build_engine(proxy_url=fallback_proxy).validate(
                    input_type=self._to_input_type(input_type),
                    content=content,
                )

        # Fallback local cuando el validador remoto bloquea con CAPTCHA
        if validation.blocked_by_schema:
            logger.warning(
                "validator.schema.org bloqueó con CAPTCHA — activando fallback local con extruct"
            )
            html_for_local = content if input_type == "html" else ""
            local_findings = validate_locally(html_for_local, base_url=content if input_type == "url" else "")
            findings = [
                RichResultsAnalysisFinding.model_validate(item.to_dict())
                for item in local_findings
            ]
            return RichResultsValidatorDetail(
                validator="schema_org",
                label="Schema.org Validator (local fallback)",
                enabled=True,
                executed=True,
                success=True,
                method_used="local_extruct",
                result_url=None,
                message="Validación local completada (validator.schema.org bloqueó con CAPTCHA)",
                error_message=validation.error_message,
                blocked=True,
                screenshots=[RichResultsScreenshot(**item) for item in validation.screenshots],
                findings=findings,
                findings_summary=self._build_findings_summary(findings),
                html_content=None,
            )

        findings = [
            RichResultsAnalysisFinding.model_validate(item.to_dict())
            for item in analyze_schema_org_html(validation.html_content or "")
        ]
        return RichResultsValidatorDetail(
            validator="schema_org",
            label="Schema.org Validator",
            enabled=True,
            executed=True,
            success=validation.is_success,
            method_used=validation.method_used,
            result_url=None,
            message=self._build_message(validation.is_success, validation.error_message),
            error_message=validation.error_message,
            blocked=validation.blocked_by_schema,
            screenshots=[RichResultsScreenshot(**item) for item in validation.screenshots],
            findings=findings,
            findings_summary=self._build_findings_summary(findings),
            html_content=validation.html_content,
        )
