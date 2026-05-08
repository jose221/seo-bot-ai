"""
Fallback local para validación de Schema.org.

Cuando validator.schema.org bloquea con CAPTCHA, este módulo extrae y valida
los schemas directamente desde el HTML usando extruct + el pipeline de validadores
local (SchemaValidatorPipeline), generando SchemaOrgHtmlFinding compatibles con
el resto del sistema.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.shared.schema_org_html_analyzer import SchemaOrgHtmlFinding

logger = logging.getLogger(__name__)


def _extract_schemas(html: str, base_url: str = "") -> List[Dict[str, Any]]:
    """Extrae schemas JSON-LD, Microdata y RDFa del HTML usando extruct."""
    try:
        import extruct
        data = extruct.extract(
            html,
            base_url=base_url or "https://example.com",
            syntaxes=["json-ld", "microdata", "rdfa"],
            uniform=True,
        )
        schemas: List[Dict[str, Any]] = []
        for syntax in ("json-ld", "microdata", "rdfa"):
            schemas.extend(data.get(syntax, []))
        return schemas
    except Exception as exc:
        logger.warning("extruct falló, intentando fallback manual: %s", exc)

    # Fallback manual: solo JSON-LD via BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or ""
            if raw.strip():
                try:
                    schemas.append(json.loads(raw.strip()))
                except Exception:
                    pass
        return schemas
    except Exception as exc:
        logger.error("Fallback manual de extracción también falló: %s", exc)
        return []


def _get_type_label(schema: Dict[str, Any]) -> str:
    t = schema.get("@type", "Unknown")
    if isinstance(t, list):
        t = t[0] if t else "Unknown"
    return str(t)


def _severity_and_color(errors: int, warnings: int):
    if errors > 0:
        return "error", "red"
    if warnings > 0:
        return "warning", "yellow"
    return "info", "green"


def validate_locally(
    html: str,
    base_url: str = "",
) -> List[SchemaOrgHtmlFinding]:
    """
    Extrae schemas del HTML y los valida localmente.
    Devuelve una lista de SchemaOrgHtmlFinding equivalente a la que
    produciría analyze_schema_org_html() sobre el HTML del validador remoto.
    """
    from app.services.schema_validators import SchemaValidatorPipeline

    schemas = _extract_schemas(html, base_url)
    findings: List[SchemaOrgHtmlFinding] = []

    if not schemas:
        findings.append(SchemaOrgHtmlFinding(
            key="schema-org-local-no-schemas",
            code="info",
            severity="info",
            category="summary",
            selector="script[type='application/ld+json']",
            message="No se encontraron schemas estructurados en el HTML (JSON-LD, Microdata, RDFa)",
            color="green",
        ))
        return findings

    pipeline = SchemaValidatorPipeline()
    total_errors = 0
    total_warnings = 0

    for idx, schema in enumerate(schemas):
        schema_type = _get_type_label(schema)
        label = f"schema[{idx}]"

        result = pipeline.run(schema, label=label)
        err_count: int = result.get("total_errors", 0)
        warn_count: int = result.get("total_warnings", 0)
        total_errors += err_count
        total_warnings += warn_count

        severity, color = _severity_and_color(err_count, warn_count)
        counter_parts = []
        if err_count:
            counter_parts.append(f"{err_count} ERROR{'ES' if err_count > 1 else ''}")
        if warn_count:
            counter_parts.append(f"{warn_count} ADVERTENCIA{'S' if warn_count > 1 else ''}")
        if not counter_parts:
            counter_parts.append("Sin errores")

        # Finding de tipo detectado
        findings.append(SchemaOrgHtmlFinding(
            key="schema-org-item-type",
            code=severity,
            severity="info",
            category="detected_type",
            selector="script[type='application/ld+json']",
            message=schema_type,
            item_name=schema_type,
            color=color,
        ))

        # Finding de estado del item
        findings.append(SchemaOrgHtmlFinding(
            key="schema-org-item-status",
            code=severity,
            severity=severity,
            category="status",
            selector="script[type='application/ld+json']",
            message=" · ".join(counter_parts),
            item_name=schema_type,
            color=color,
        ))

        # Findings de errores individuales
        for validator_result in result.get("validators", []):
            for error in validator_result.get("errors", []):
                findings.append(SchemaOrgHtmlFinding(
                    key="schema-org-local-error",
                    code="error",
                    severity="error",
                    category="validation_error",
                    selector="script[type='application/ld+json']",
                    message=error.get("message", "Error desconocido"),
                    item_name=schema_type,
                    color="red",
                ))
            for warning in validator_result.get("warnings", []):
                lvl = warning.get("level", "WARNING")
                if lvl == "INFO":
                    continue
                findings.append(SchemaOrgHtmlFinding(
                    key="schema-org-local-warning",
                    code="warning",
                    severity="warning",
                    category="validation_warning",
                    selector="script[type='application/ld+json']",
                    message=warning.get("message", "Advertencia desconocida"),
                    item_name=schema_type,
                    color="yellow",
                ))

    # Resumen global al inicio
    global_severity, global_color = _severity_and_color(total_errors, total_warnings)
    summary_parts = [f"{len(schemas)} ELEMENTO{'S' if len(schemas) > 1 else ''}"]
    if total_errors:
        summary_parts.append(f"{total_errors} ERROR{'ES' if total_errors > 1 else ''}")
    if total_warnings:
        summary_parts.append(f"{total_warnings} ADVERTENCIA{'S' if total_warnings > 1 else ''}")

    findings.insert(0, SchemaOrgHtmlFinding(
        key="schema-org-summary",
        code=global_severity,
        severity=global_severity,
        category="summary",
        selector="body",
        message=" · ".join(summary_parts),
        color=global_color,
    ))

    return findings
