from app.shared.rich_results_html_analyzer import (
    analyze_rich_results_html,
    build_rich_results_findings_summary,
)


def test_analyze_validation_html_extracts_findings_and_documents():
    html = """
    <div class="cHUf9c gf803d airlR mPxjoe CDUYmb">
      <div class="cbZz9b RSZNi CY0Maf-bMElCd">Falta el campo "review" (opcional)</div>
      <a class="FKF6mc TpQm9d" href="https://developers.google.com/search/docs/appearance/structured-data/product-snippet" target="_blank" aria-label="Consultar documentación del problema"></a>
    </div>
    <div class="Nn9qof GBCubb" title="Detectados problemas no críticos">Detectados problemas no críticos</div>
    <div class="MreLB QrfJGb">Fragmentos de productos</div>
    """

    findings = analyze_rich_results_html(html)
    summary = build_rich_results_findings_summary(findings)

    assert len(findings) == 3
    assert any(
        finding.message == 'Falta el campo "review" (opcional)'
        and finding.severity == "warning"
        and finding.document_url == "https://developers.google.com/search/docs/appearance/structured-data/product-snippet"
        for finding in findings
    )
    assert any(
        finding.message == "Detectados problemas no críticos"
        and finding.category == "summary"
        for finding in findings
    )
    assert any(
        finding.message == "Fragmentos de productos"
        and finding.category == "detected_type"
        for finding in findings
    )
    assert summary.total == 3
    assert summary.by_severity == {"warning": 1, "info": 2}
