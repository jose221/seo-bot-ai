"""
Servicio para generar reportes de Google Rich Results.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import unquote, urlparse

import trafilatura
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.core.config import settings
from app.handlers.seo_scrapper.google_rich_results_engine import (
    GoogleRichResultsEngine,
    InputType,
)
from app.schemas.rich_results_schemas import (
    RichResultsAIResult,
    RichResultsReportRequest,
    RichResultsReportResponse,
)
from app.services.ai_client import get_ai_client


class RichResultsService:
    def __init__(self) -> None:
        self.ai_client = get_ai_client()

    def _resolve_proxy_url(self) -> Optional[str]:
        if settings.RICH_RESULTS_PROXY_URL and settings.RICH_RESULTS_PROXY_URL.strip():
            return settings.RICH_RESULTS_PROXY_URL.strip()
        return None

    def _build_engine(self, proxy_url: Optional[str]) -> GoogleRichResultsEngine:
        parsed_proxy_config = None
        proxy_server = None

        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_server = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                proxy_server = f"{proxy_server}:{parsed.port}"

            parsed_proxy_config = {"server": proxy_server}
            if parsed.username:
                parsed_proxy_config["username"] = unquote(parsed.username)
            if parsed.password:
                parsed_proxy_config["password"] = unquote(parsed.password)

        return GoogleRichResultsEngine(
            proxy_config=parsed_proxy_config,
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

    async def report_page(
        self,
        payload: RichResultsReportRequest,
        token: Optional[str] = None,
    ) -> RichResultsReportResponse:
        input_type = InputType.URL if payload.is_url else InputType.HTML
        content = payload.content
        proxy_url = self._resolve_proxy_url()
        engine = self._build_engine(proxy_url)

        validation = await engine.validate(input_type=input_type, content=content or "")
        ai_result: Optional[RichResultsAIResult] = None
        ai_error_message: Optional[str] = None

        if payload.get_ai_result and validation.is_success and validation.html_content and not validation.blocked_by_google:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Se requiere un token válido para obtener get_ai_result"
                )

            markdown_content = self._html_to_markdown(validation.html_content)
            if markdown_content:
                try:
                    ai_payload = await self.ai_client.analyze_rich_results_content(
                        markdown_content=markdown_content,
                        rich_results_url=validation.result_url,
                        source_url=payload.content if payload.is_url else None,
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
            get_ai_result=ai_result,
            ai_error_message=ai_error_message
        )


_rich_results_service: Optional[RichResultsService] = None


def get_rich_results_service() -> RichResultsService:
    global _rich_results_service
    if _rich_results_service is None:
        _rich_results_service = RichResultsService()
    return _rich_results_service
