from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class RichResultsHtmlAnalysisRule:
    key: str
    selectors: tuple[str, ...]
    code: str
    severity: str
    category: str
    text_selectors: tuple[str, ...] = ()
    text_mode: str = "text"
    document_selectors: tuple[str, ...] = ("a[href]",)


@dataclass(frozen=True)
class RichResultsHtmlFinding:
    key: str
    code: str
    severity: str
    category: str
    selector: str
    message: str
    document_url: Optional[str] = None
    document_label: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RichResultsHtmlFindingSummary:
    total: int
    by_severity: dict[str, int]
    by_category: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


HTML_ANALYSIS_RULES: tuple[RichResultsHtmlAnalysisRule, ...] = (
    RichResultsHtmlAnalysisRule(
        key="missing-optional-field",
        selectors=("div.gf803d", "div.O5XGUb"),
        code="warning",
        severity="warning",
        category="issue",
        text_selectors=(
            ".cbZz9b.RSZNi.CY0Maf-bMElCd",
            ".cbZz9b.RSZNi",
            ".cbZz9b",
        ),
    ),
    RichResultsHtmlAnalysisRule(
        key="non-critical-issues-detected",
        selectors=("div.Nn9qof.GBCubb",),
        code="info",
        severity="info",
        category="summary",
        text_mode="title_or_text",
    ),
    RichResultsHtmlAnalysisRule(
        key="detected-rich-result-type",
        selectors=("div.MreLB.QrfJGb", "div.MreLB.jdejT"),
        code="info",
        severity="info",
        category="detected_type",
    ),
)


def _normalize_text(value: Optional[str]) -> str:
    return " ".join((value or "").split()).strip()


def _extract_rule_message(element, rule: RichResultsHtmlAnalysisRule) -> str:
    for selector in rule.text_selectors:
        matched = element.select_one(selector)
        if matched:
            message = _normalize_text(matched.get_text(" ", strip=True))
            if message:
                return message

    if rule.text_mode == "title_or_text":
        title = _normalize_text(element.get("title"))
        if title:
            return title

    return _normalize_text(element.get_text(" ", strip=True))


def _extract_rule_document(
    element,
    rule: RichResultsHtmlAnalysisRule,
) -> tuple[Optional[str], Optional[str]]:
    for selector in rule.document_selectors:
        matched = element.select_one(selector)
        if not matched:
            continue

        href = _normalize_text(matched.get("href"))
        label = _normalize_text(
            matched.get("aria-label") or matched.get_text(" ", strip=True)
        )
        if href:
            return href, label or None

    return None, None


def analyze_rich_results_html(html_content: str) -> list[RichResultsHtmlFinding]:
    if not html_content or not html_content.strip():
        return []

    soup = BeautifulSoup(html_content, "lxml")
    findings: list[RichResultsHtmlFinding] = []
    seen: set[tuple[str, str, str, str, Optional[str]]] = set()

    for rule in HTML_ANALYSIS_RULES:
        for selector in rule.selectors:
            for element in soup.select(selector):
                message = _extract_rule_message(element, rule)
                if not message:
                    continue

                document_url, document_label = _extract_rule_document(element, rule)
                fingerprint = (
                    rule.key,
                    rule.code,
                    rule.severity,
                    message,
                    document_url,
                )
                if fingerprint in seen:
                    continue

                seen.add(fingerprint)
                findings.append(
                    RichResultsHtmlFinding(
                        key=rule.key,
                        code=rule.code,
                        severity=rule.severity,
                        category=rule.category,
                        selector=selector,
                        message=message,
                        document_url=document_url,
                        document_label=document_label,
                    )
                )

    return findings


def build_rich_results_findings_summary(
    findings: list[RichResultsHtmlFinding],
) -> RichResultsHtmlFindingSummary:
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}

    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_category[finding.category] = by_category.get(finding.category, 0) + 1

    return RichResultsHtmlFindingSummary(
        total=len(findings),
        by_severity=by_severity,
        by_category=by_category,
    )
