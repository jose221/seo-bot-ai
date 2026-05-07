from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


GOOGLE_RICH_RESULTS_BASE_URL = "https://search.google.com"


@dataclass(frozen=True)
class RichResultsHtmlAnalysisRule:
    key: str
    selectors: tuple[str, ...]
    category: str
    item_name_selectors: tuple[str, ...] = ()
    message_selectors: tuple[str, ...] = ()
    warning_selectors: tuple[str, ...] = ()
    icon_selectors: tuple[str, ...] = ()
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
    element_url: Optional[str] = None
    item_name: Optional[str] = None
    color: Optional[str] = None

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
        key="rich-result-card",
        selectors=("span.YtFhsc",),
        category="rich_result_card",
        item_name_selectors=(
            "div.MreLB.QrfJGb",
        ),
        message_selectors=(
            "div.pmpmLd > div.MreLB.jdejT",
            "div.pmpmLd div.MreLB.jdejT",
        ),
        warning_selectors=(
            "div.Nn9qof.GBCubb",
        ),
        icon_selectors=(
            "div.XrLUHe span.DPvwYc",
        ),
    ),
)


def _normalize_text(value: Optional[str]) -> str:
    return " ".join((value or "").split()).strip()


def _normalize_google_url(value: Optional[str]) -> Optional[str]:
    href = _normalize_text(value)
    if not href:
        return None
    return urljoin(f"{GOOGLE_RICH_RESULTS_BASE_URL}/", href)


def _extract_first_text(element, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        matched = element.select_one(selector)
        if matched:
            text = _normalize_text(matched.get_text(" ", strip=True))
            if text:
                return text
    return ""


def _extract_status_text(element, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        matched = element.select_one(selector)
        if not matched:
            continue

        direct_div = matched.find("div", recursive=False)
        if direct_div:
            text = _normalize_text(direct_div.get_text(" ", strip=True))
            if text:
                return text

        text = _normalize_text(matched.get_text(" ", strip=True))
        if text:
            return text

    return ""


def _extract_rule_document(
    element,
    rule: RichResultsHtmlAnalysisRule,
) -> tuple[Optional[str], Optional[str]]:
    for selector in rule.document_selectors:
        matched = element.select_one(selector)
        if not matched:
            continue

        href = _normalize_google_url(matched.get("href"))
        label = _normalize_text(
            matched.get("aria-label") or matched.get_text(" ", strip=True)
        )
        if href:
            return href, label or None

    return None, None


def _extract_warning_text(element, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        matched = element.select_one(selector)
        if matched:
            title = _normalize_text(matched.get("title"))
            text = _normalize_text(matched.get_text(" ", strip=True))
            if title:
                return title
            if text:
                return text
    return ""


def _resolve_icon_state(icon_text: str) -> tuple[str, str, str]:
    normalized_icon = _normalize_text(icon_text).lower()
    icon_map = {
        "check_circle": ("valid", "info", "green"),
        "warning": ("warning", "warning", "yellow"),
        "error": ("error", "error", "red"),
        "cancel": ("error", "error", "red"),
        "dangerous": ("error", "error", "red"),
    }
    return icon_map.get(normalized_icon, ("info", "info", "gray"))


def analyze_rich_results_html(html_content: str) -> list[RichResultsHtmlFinding]:
    if not html_content or not html_content.strip():
        return []

    soup = BeautifulSoup(html_content, "lxml")
    findings: list[RichResultsHtmlFinding] = []
    seen: set[tuple[str, str, str, str, Optional[str], Optional[str]]] = set()

    for rule in HTML_ANALYSIS_RULES:
        for selector in rule.selectors:
            for element in soup.select(selector):
                item_name = _extract_first_text(element, rule.item_name_selectors)
                status_message = _extract_status_text(element, rule.message_selectors)
                warning_message = _extract_warning_text(element, rule.warning_selectors)
                icon_text = _extract_first_text(element, rule.icon_selectors)
                document_url, document_label = _extract_rule_document(element, rule)
                code, severity, color = _resolve_icon_state(icon_text)

                if not item_name and not status_message and not warning_message:
                    continue

                extracted_findings: list[RichResultsHtmlFinding] = []
                if item_name:
                    extracted_findings.append(
                        RichResultsHtmlFinding(
                            key="rich-result-type",
                            code=code,
                            severity="info",
                            category="detected_type",
                            selector=selector,
                            message=item_name,
                            document_url=document_url,
                            document_label=document_label,
                            element_url=document_url,
                            item_name=item_name,
                            color=color,
                        )
                    )

                if status_message:
                    extracted_findings.append(
                        RichResultsHtmlFinding(
                            key="rich-result-status",
                            code=code,
                            severity=severity,
                            category="status",
                            selector=selector,
                            message=status_message,
                            document_url=document_url,
                            document_label=document_label,
                            element_url=document_url,
                            item_name=item_name or None,
                            color=color,
                        )
                    )

                if warning_message:
                    extracted_findings.append(
                        RichResultsHtmlFinding(
                            key="rich-result-warning",
                            code="warning",
                            severity="warning",
                            category="warning",
                            selector=selector,
                            message=warning_message,
                            document_url=document_url,
                            document_label=document_label,
                            element_url=document_url,
                            item_name=item_name or None,
                            color="yellow",
                        )
                    )

                for finding in extracted_findings:
                    fingerprint = (
                        finding.key,
                        finding.code,
                        finding.severity,
                        finding.message,
                        finding.document_url,
                        finding.item_name,
                    )
                    if fingerprint in seen:
                        continue
                    seen.add(fingerprint)
                    findings.append(finding)

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
