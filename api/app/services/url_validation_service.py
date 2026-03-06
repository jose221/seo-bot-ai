"""
Servicio para validación batch de schemas por URL.
Extrae schemas, los compara contra un source, y genera análisis IA por URL.
"""
import re
from typing import Any, Dict, List, Optional

from app.services.ai_client import AIClient
from app.services.audit_engine import get_audit_engine
from app.services.seo_analyzer import SEOAnalyzer
from app.services.schema_audit_service import get_schema_audit_service
from app.schemas.ai_schemas import ChatMessage, MessageRole, ChatCompletionRequest


# Orden de severidad para compute_global_severity
_SEVERITY_ORDER = {"ok": 0, "warning": 1, "critical": 2}
_SEVERITY_REVERSE = {0: "ok", 1: "warning", 2: "critical"}


class UrlValidationService:
    """
    Orquesta la validación de schemas para una lista de URLs.
    Responsabilidades:
      - Parseo de URLs (separadas por \\n, coma o espacio).
      - Extracción de schemas por URL via AuditEngine + SEOAnalyzer.
      - Generación de análisis IA por URL.
      - Cálculo de severidad global.
    """

    def __init__(self):
        self.ai_client = AIClient()
        self._schema_service = get_schema_audit_service()

    # ------------------------------------------------------------------
    # Parseo de URLs
    # ------------------------------------------------------------------

    @staticmethod
    def parse_urls(raw: str) -> List[str]:
        """
        Separa un string de URLs por salto de línea, coma o espacio.
        Limpia, deduplica y valida que parezcan URLs.

        Args:
            raw: String con URLs separadas por \\n, coma o espacio.

        Returns:
            Lista de URLs únicas y limpias.
        """
        if not raw or not raw.strip():
            return []

        # Separar por newline, coma o espacio
        parts = re.split(r'[\n,\s]+', raw.strip())

        seen = set()
        urls: List[str] = []

        for part in parts:
            cleaned = part.strip()
            if not cleaned:
                continue
            # Validación básica: debe empezar con http(s)
            if not cleaned.startswith(("http://", "https://")):
                continue
            if cleaned not in seen:
                seen.add(cleaned)
                urls.append(cleaned)

        return urls

    # ------------------------------------------------------------------
    # Extracción de schemas
    # ------------------------------------------------------------------

    async def fetch_schema_for_url(
        self,
        url: str,
        timeout_ms: int = 30_000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el HTML de una URL via AuditEngine.fetch_html y
        extrae los schemas con SEOAnalyzer.extract_schemas_from_html.

        Args:
            url: URL a analizar.
            timeout_ms: Timeout máximo en milisegundos.

        Returns:
            Lista de schemas encontrados. Vacía si hay error.
        """
        engine = get_audit_engine()
        html = await engine.fetch_html(url, timeout_ms=timeout_ms)
        if not html:
            return []
        return SEOAnalyzer.extract_schemas_from_html(html, url)

    # ------------------------------------------------------------------
    # Análisis IA por URL
    # ------------------------------------------------------------------

    async def generate_url_analysis_ai(
        self,
        url: str,
        url_schema: Any,
        proposed_schema: Any,
        validation_errors: Optional[Dict[str, Any]],
        name_validation: str,
        description_validation: Optional[str],
        ai_instruction: Optional[str],
        token: str,
    ) -> Dict[str, Any]:
        """
        Genera el análisis IA para una URL individual.

        Args:
            url: URL analizada.
            url_schema: Schema detectado en la URL (ya minificado).
            proposed_schema: Schema propuesto del source (ya minificado).
            validation_errors: Resultado de validate_schema_payload.
            name_validation: Nombre del flujo.
            description_validation: Descripción del flujo.
            ai_instruction: Instrucción adicional del usuario.
            token: Token de autenticación para la API de IA.

        Returns:
            Dict con 'content' (texto IA) y 'usage' (tokens).
        """
        template = self.ai_client.jinja_env.get_template("url_schema_validator.jinja")

        prompt_content = template.render(
            url=url,
            url_schema=self._schema_service._minify_schema_for_ai(url_schema),
            proposed_schema=self._schema_service._minify_schema_for_ai(proposed_schema),
            validation_errors=validation_errors,
            name_validation=name_validation,
            description_validation=description_validation or "",
            ai_instruction=ai_instruction or "",
        )

        request = ChatCompletionRequest(
            messages=[ChatMessage(role=MessageRole.USER, content=prompt_content)],
            model="deepseek-chat",
            stream=False,
        )

        input_tokens = self.ai_client.count_tokens(prompt_content)
        response = await self.ai_client.chat_completion(request, token)
        content = response.get_content()
        output_tokens = self.ai_client.count_tokens(content)

        return {
            "content": content,
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        }

    # ------------------------------------------------------------------
    # Validación estructural
    # ------------------------------------------------------------------

    def validate_url_schema(self, schema: Any, url: str) -> Dict[str, Any]:
        """
        Valida un schema usando la lógica existente de SchemaAuditService.

        Args:
            schema: Schema detectado en la URL.
            url: URL (usada como label).

        Returns:
            Resultado de validación con is_valid, errors, warnings.
        """
        return self._schema_service.validate_schema_payload(schema, label=url)

    # ------------------------------------------------------------------
    # Severidad
    # ------------------------------------------------------------------

    @staticmethod
    def extract_severity_from_ai(ai_content: str) -> str:
        """
        Extrae la severidad desde el texto de la IA.
        Busca patrones como 'Severidad: critical', 'Severidad: warning', etc.

        Args:
            ai_content: Texto de respuesta de la IA.

        Returns:
            'ok', 'warning' o 'critical'.
        """
        if not ai_content:
            return "warning"

        content_lower = ai_content.lower()

        # Buscar patrón explícito
        match = re.search(r'severidad:\s*(ok|warning|critical)', content_lower)
        if match:
            return match.group(1)

        # Heurística: si menciona "critical" o "critico" en contexto de severidad
        if "critical" in content_lower or "critico" in content_lower:
            return "critical"
        if "warning" in content_lower or "advertencia" in content_lower:
            return "warning"

        return "ok"

    @staticmethod
    def compute_global_severity(results: List[Dict[str, Any]]) -> str:
        """
        Calcula la severidad global como el peor caso entre todas las URLs.
        Ignora entradas con error.

        Args:
            results: Lista de resultados por URL.

        Returns:
            'ok', 'warning' o 'critical'.
        """
        max_severity = 0

        for result in results:
            if result.get("error"):
                continue
            severity = result.get("severity", "ok")
            max_severity = max(max_severity, _SEVERITY_ORDER.get(severity, 0))

        return _SEVERITY_REVERSE.get(max_severity, "ok")

    # ------------------------------------------------------------------
    # Generación de Markdown consolidado para reportes
    # ------------------------------------------------------------------

    @staticmethod
    def build_consolidated_markdown(
        results: List[Dict[str, Any]],
        name_validation: str,
        description_validation: Optional[str],
        global_severity: str,
    ) -> str:
        """
        Construye un texto Markdown consolidado con secciones por URL
        para generación de PDF/Word.

        Args:
            results: Lista de resultados por URL.
            name_validation: Nombre del flujo.
            description_validation: Descripción del flujo.
            global_severity: Severidad global calculada.

        Returns:
            Texto Markdown listo para generar reportes.
        """
        lines: List[str] = []

        lines.append(f"# Validación de Schemas por URL: {name_validation}")
        lines.append("")

        if description_validation:
            lines.append(f"**Descripción:** {description_validation}")
            lines.append("")

        lines.append(f"**Severidad Global:** {global_severity.upper()}")
        lines.append(f"**Total URLs analizadas:** {len(results)}")
        lines.append("")

        # Resumen rápido
        ok_count = sum(1 for r in results if r.get("severity") == "ok" and not r.get("error"))
        warn_count = sum(1 for r in results if r.get("severity") == "warning" and not r.get("error"))
        crit_count = sum(1 for r in results if r.get("severity") == "critical" and not r.get("error"))
        err_count = sum(1 for r in results if r.get("error"))

        lines.append("## Resumen")
        lines.append("")
        lines.append(f"| Estado | Cantidad |")
        lines.append(f"|--------|----------|")
        lines.append(f"| Ok | {ok_count} |")
        lines.append(f"| Warning | {warn_count} |")
        lines.append(f"| Critical | {crit_count} |")
        lines.append(f"| Error (no procesadas) | {err_count} |")
        lines.append("")

        # Detalle por URL
        lines.append("---")
        lines.append("")

        for idx, result in enumerate(results, 1):
            url = result.get("url", "URL desconocida")
            lines.append(f"## {idx}. {url}")
            lines.append("")

            if result.get("error"):
                lines.append(f"**Error:** {result.get('error')}")
                lines.append("")
                lines.append("---")
                lines.append("")
                continue

            severity = result.get("severity", "ok")
            lines.append(f"**Severidad:** {severity.upper()}")
            lines.append("")

            # Tipos detectados
            types_found = result.get("schema_types_found", [])
            if types_found:
                lines.append(f"**Tipos de Schema detectados:** {', '.join(types_found)}")
            else:
                lines.append("**Tipos de Schema detectados:** Ninguno")
            lines.append("")

            # Análisis IA
            ai_report = result.get("ai_report", "")
            if ai_report:
                lines.append(ai_report)
            else:
                lines.append("*Sin análisis de IA disponible.*")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_url_validation_service: Optional[UrlValidationService] = None


def get_url_validation_service() -> UrlValidationService:
    global _url_validation_service
    if _url_validation_service is None:
        _url_validation_service = UrlValidationService()
    return _url_validation_service

