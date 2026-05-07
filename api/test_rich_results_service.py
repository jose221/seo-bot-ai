from app.shared.rich_results_html_analyzer import (
    analyze_rich_results_html,
    build_rich_results_findings_summary,
)


def test_analyze_validation_html_extracts_findings_and_documents():
    html = """
    <span jscontroller="ZjYfdb" class="YtFhsc">
      <div role="presentation" class="U26fgb O0WRkf oG5Srb C0oVfc IrAVOe M9Bg4d">
        <a class="FKF6mc TpQm9d" href="./test/rich-results/result/r%2Fproduct?id=abc123">
          <span class="RveJvd snByac">
            <div class="HS72Xd">
              <div class="XrLUHe"><span class="DPvwYc CADyfd ctLDId sWvkTd" aria-hidden="true">check_circle</span></div>
              <div class="pmpmLd">
                <div class="MreLB QrfJGb">Fragmentos de productos</div>
                <div class="MreLB jdejT J2NIdd">
                  <div>Se ha detectado 1 elemento válido</div>
                  <div class="xyltVc">
                    <div class="Nn9qof GBCubb" title="Detectados problemas no críticos">Detectados problemas no críticos</div>
                  </div>
                </div>
              </div>
            </div>
          </span>
        </a>
      </div>
    </span>
    """

    findings = analyze_rich_results_html(html)
    summary = build_rich_results_findings_summary(findings)

    assert len(findings) == 3
    assert any(
        finding.message == "Fragmentos de productos"
        and finding.category == "detected_type"
        and finding.color == "green"
        and finding.element_url == "https://search.google.com/test/rich-results/result/r%2Fproduct?id=abc123"
        for finding in findings
    )
    assert any(
        finding.message == "Se ha detectado 1 elemento válido"
        and finding.category == "status"
        and finding.code == "valid"
        and finding.item_name == "Fragmentos de productos"
        for finding in findings
    )
    assert any(
        finding.message == "Detectados problemas no críticos"
        and finding.category == "warning"
        and finding.color == "yellow"
        for finding in findings
    )
    assert summary.total == 3
    assert summary.by_severity == {"info": 2, "warning": 1}
