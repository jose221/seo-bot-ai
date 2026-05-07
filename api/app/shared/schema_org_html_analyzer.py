from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class SchemaOrgHtmlFinding:
    key: str
    code: str
    severity: str
    category: str
    selector: str
    message: str
    document_url: Optional[str] = None
    document_label: Optional[str] = None
    element_url: Optional[str] = None
    item_name: Optional[str] = None
    color: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SchemaOrgHtmlFindingSummary:
    total: int
    by_severity: dict[str, int]
    by_category: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_text(value: Optional[str]) -> str:
    return " ".join((value or "").split()).strip()


def _parse_counters(texts: list[str]) -> tuple[int, int, int]:
    errors = 0
    warnings = 0
    items = 0
    for text in texts:
        normalized = _normalize_text(text).upper()
        parts = normalized.split(" ", 1)
        if not parts or not parts[0].isdigit():
            continue
        value = int(parts[0])
        if "ERROR" in normalized:
            errors = value
        elif "ADVERTENCIA" in normalized:
            warnings = value
        elif "ELEMENTO" in normalized:
            items = value
    return errors, warnings, items


def _resolve_counts_state(errors: int, warnings: int) -> tuple[str, str, str]:
    if errors > 0:
        return "error", "error", "red"
    if warnings > 0:
        return "warning", "warning", "yellow"
    return "valid", "info", "green"


def analyze_schema_org_html(html_content: str) -> list[SchemaOrgHtmlFinding]:
    if not html_content or not html_content.strip():
        return []

    soup = BeautifulSoup(html_content, "lxml")
    findings: list[SchemaOrgHtmlFinding] = []
    seen: set[tuple[str, str, str, str, Optional[str]]] = set()

    for block in soup.select("div.sKfxWe-BeDmAc.sKfxWe-BeDmAc-AHe6Kc"):
        status_label = _normalize_text(
            block.select_one("div.sKfxWe-BeDmAc-r4nke") and block.select_one("div.sKfxWe-BeDmAc-r4nke").get_text(" ", strip=True)
        )
        counter_texts = [
            _normalize_text(node.get_text(" ", strip=True))
            for node in block.select("div.sKfxWe-BeDmAc-ma6Yeb-qwU8Me-WiHQyb span.K4efff-fmcmS")
        ]
        errors, warnings, items = _parse_counters(counter_texts)
        code, severity, color = _resolve_counts_state(errors, warnings)
        summary_message = " · ".join(filter(None, counter_texts))

        if summary_message:
            findings.append(
                SchemaOrgHtmlFinding(
                    key="schema-org-summary",
                    code=code,
                    severity=severity,
                    category="summary",
                    selector="div.sKfxWe-BeDmAc.sKfxWe-BeDmAc-AHe6Kc",
                    message=summary_message,
                    item_name=status_label or None,
                    color=color,
                )
            )

        for item in block.select("li.mdl-list__item.aVTXAb-BeDmAc-JNdkSc-rTEl-x3Eknd"):
            item_name = _normalize_text(
                item.select_one("span.mdl-list__item-primary-content")
                and item.select_one("span.mdl-list__item-primary-content").get_text(" ", strip=True)
            )
            item_counter_texts = [
                _normalize_text(node.get_text(" ", strip=True))
                for node in item.select("span.K4efff-fmcmS")
            ]
            item_errors, item_warnings, _ = _parse_counters(item_counter_texts)
            item_code, item_severity, item_color = _resolve_counts_state(item_errors, item_warnings)
            item_message = " · ".join(filter(None, item_counter_texts))

            if item_name:
                finding = SchemaOrgHtmlFinding(
                    key="schema-org-item-type",
                    code=item_code,
                    severity="info",
                    category="detected_type",
                    selector="li.mdl-list__item.aVTXAb-BeDmAc-JNdkSc-rTEl-x3Eknd",
                    message=item_name,
                    item_name=item_name,
                    color=item_color,
                )
                fingerprint = (finding.key, finding.code, finding.severity, finding.message, finding.item_name)
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    findings.append(finding)

            if item_message:
                finding = SchemaOrgHtmlFinding(
                    key="schema-org-item-status",
                    code=item_code,
                    severity=item_severity,
                    category="status",
                    selector="li.mdl-list__item.aVTXAb-BeDmAc-JNdkSc-rTEl-x3Eknd",
                    message=item_message,
                    item_name=item_name or None,
                    color=item_color,
                )
                fingerprint = (finding.key, finding.code, finding.severity, finding.message, finding.item_name)
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    findings.append(finding)

    return findings


def build_schema_org_findings_summary(
    findings: list[SchemaOrgHtmlFinding],
) -> SchemaOrgHtmlFindingSummary:
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}

    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_category[finding.category] = by_category.get(finding.category, 0) + 1

    return SchemaOrgHtmlFindingSummary(
        total=len(findings),
        by_severity=by_severity,
        by_category=by_category,
    )
