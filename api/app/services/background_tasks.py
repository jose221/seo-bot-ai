"""
Servicio centralizado para tareas en segundo plano.
Maneja la ejecución de auditorías y comparaciones.
"""
from uuid import UUID
from datetime import datetime, timezone
from typing import List

from app.core.database import db_manager
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.models.audit_comparison import AuditComparison, ComparisonStatus
from app.services.audit_engine import get_audit_engine
from app.services.ai_client import get_ai_client
from app.services.cache import Cache
from app.services.report_generator import ReportGenerator
from app.services.seo_analyzer import SEOAnalyzer
from app.services.audit_comparator import get_audit_comparator
from app.helpers import extract_domain
from sqlalchemy import String, cast as sql_cast, desc
from sqlalchemy.orm import joinedload
from sqlmodel import select


async def run_audit_task(
    audit_id: UUID,
    webpage: WebPage,
    include_ai: bool,
    token: str
):
    """
    Ejecutar auditoría en segundo plano.
    Centraliza la lógica de ejecución de auditorías.
    """
    audit = None
    _cache = Cache(table_name="audits_reports")

    try:
        # Actualizar estado a IN_PROGRESS
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
            if not audit:
                print(f"❌ No se encontró audit {audit_id}")
                return

            audit.status = AuditStatus.IN_PROGRESS
            session.add(audit)

        print(f"🚀 Iniciando auditoría para {webpage.url}")

        # Ejecutar auditoría con Playwright/Lighthouse
        audit_engine = get_audit_engine()
        req_lighthouse_params = dict(url=webpage.url, instructions=webpage.instructions)
        lighthouse_result = await _cache.loadFromCacheAsync(
            params=req_lighthouse_params,
            prefix="___lighthouse_report___",
            callback_async=audit_engine.run_lighthouse_audit,
            **req_lighthouse_params
        )

        # Análisis de IA si se solicita
        ai_analysis_data = None
        if include_ai:
            print(f"🤖 Ejecutando análisis de IA...")
            ai_client = get_ai_client()

            try:
                req_ai_analysis_params = dict(url=webpage.url)
                ai_analysis = await _cache.loadFromCacheAsync(
                    params=req_ai_analysis_params,
                    prefix="ai_analysis_",
                    ttl=3600,
                    callback_async=ai_client.analyze_seo_content,
                    html_content=lighthouse_result.get('html_content_raw', ''),
                    lighthouse_data={
                        'performance_score': lighthouse_result.get('performance_score'),
                        'seo_score': lighthouse_result.get('seo_score'),
                        'accessibility_score': lighthouse_result.get('accessibility_score'),
                        'lcp': lighthouse_result.get('lcp'),
                        'cls': lighthouse_result.get('cls')
                    },
                    token=token,
                    **req_ai_analysis_params
                )

                ai_analysis_data = {
                    'analysis': ai_analysis,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'model': 'deepseek-chat'
                }
            except Exception as ai_error:
                print(f"⚠️  Error en análisis de IA: {ai_error}")
                ai_analysis_data = {
                    'error': str(ai_error),
                    'status': 'failed'
                }

        # Análisis SEO
        _seo_analyzer = SEOAnalyzer(
            url=extract_domain(webpage.url),
            html_content=lighthouse_result.get('html_content_raw', '')
        )
        seo_analysis = _seo_analyzer.run_full_analysis()

        # Guardar resultados
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
            lighthouse_result.pop('html_content', None)
            lighthouse_result.pop('html_content_raw', None)

            if audit:
                audit.performance_score = lighthouse_result.get('performance_score')
                audit.seo_score = lighthouse_result.get('seo_score')
                audit.accessibility_score = lighthouse_result.get('accessibility_score')
                audit.best_practices_score = lighthouse_result.get('best_practices_score')
                audit.lcp = lighthouse_result.get('lcp')
                audit.fid = lighthouse_result.get('fid')
                audit.cls = lighthouse_result.get('cls')
                audit.lighthouse_data = lighthouse_result
                audit.ai_suggestions = ai_analysis_data
                audit.status = AuditStatus.COMPLETED
                audit.completed_at = datetime.now(timezone.utc)
                audit.seo_analysis = seo_analysis

                # Generar reporte
                report = ReportGenerator(audit=audit).generate_all()
                print(f"📄 Reporte generado: {report}")

                # Guardar rutas de los reportes generados
                audit.report_pdf_path = report.get('pdf_path')
                audit.report_excel_path = report.get('xlsx_path')
                audit.report_word_path = report.get('word_path')

                session.add(audit)

        print(f"✅ Auditoría completada: {audit_id}")

    except Exception as e:
        print(f"❌ Error en auditoría {audit_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Guardar estado de error
        try:
            with db_manager.sync_session_context() as session:
                if audit is None:
                    audit = session.get(AuditReport, audit_id)

                if audit:
                    audit.status = AuditStatus.FAILED
                    audit.error_message = str(e)
                    audit.completed_at = datetime.now(timezone.utc)
                    session.add(audit)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo: {inner_error}")


async def run_comparison_task(
    comparison_id: UUID,
    base_web_page_id: UUID,
    competitor_ids: List[UUID],
    include_ai: bool,
    token: str,
    user_id: UUID
):
    """
    Ejecutar comparación de auditorías en segundo plano.
    """
    comparison = None
    _cache = Cache(table_name="audits_reports_compare_")

    try:
        # Actualizar estado a IN_PROGRESS
        with db_manager.sync_session_context() as session:
            comparison = session.get(AuditComparison, comparison_id)
            if not comparison:
                print(f"❌ No se encontró comparison {comparison_id}")
                return

            comparison.status = ComparisonStatus.IN_PROGRESS
            session.add(comparison)

        print(f"🚀 Iniciando comparación {comparison_id}")

        # Obtener página base y su auditoría
        with db_manager.sync_session_context() as session:
            base_webpage = session.get(WebPage, base_web_page_id)
            if not base_webpage:
                raise Exception("Página base no encontrada")

            # Obtener última auditoría completada de la página base
            base_audit_stmt = select(AuditReport).options(joinedload(AuditReport.web_page)).where(
                AuditReport.web_page_id == base_web_page_id,
                sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
            ).order_by(desc(AuditReport.created_at)).limit(1)

            base_audit_result = session.execute(base_audit_stmt)
            base_audit = base_audit_result.scalars().first()

            if not base_audit:
                raise Exception(f"No hay auditorías completadas para {base_webpage.url}")

        # Procesar comparaciones
        comparator = get_audit_comparator()
        comparisons = []
        competitors_audit = []

        with db_manager.sync_session_context() as session:
            for competitor_id in competitor_ids:
                try:
                    competitor_webpage = session.get(WebPage, competitor_id)
                    if not competitor_webpage:
                        print(f"⚠️  Target {competitor_id} no encontrado")
                        continue

                    # Obtener auditoría del competidor
                    competitor_audit_stmt = select(AuditReport).options(joinedload(AuditReport.web_page)).where(
                        AuditReport.web_page_id == competitor_id,
                        sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
                    ).order_by(desc(AuditReport.created_at)).limit(1)

                    competitor_audit_result = session.execute(competitor_audit_stmt)
                    competitor_audit = competitor_audit_result.scalars().first()

                    if not competitor_audit:
                        print(f"⚠️  No hay auditoría para {competitor_webpage.url}")
                        continue

                    # Generar comparación
                    comparison_report = comparator.generate_comparison_report(
                        base_audit=base_audit,
                        compare_audit=competitor_audit,
                        base_url=base_webpage.url,
                        compare_url=competitor_webpage.url
                    )

                    # Análisis de IA si se solicita
                    if include_ai and token:
                        try:
                            req_ai_analysis_params = dict(
                                base_url=base_webpage.url,
                                compare_url=competitor_webpage.url
                            )
                            ai_analysis = await _cache.loadFromCacheAsync(
                                params=req_ai_analysis_params,
                                prefix="ai_analysis_compare_",
                                ttl=36000,
                                callback_async=comparator.generate_ai_comparison,
                                **req_ai_analysis_params,
                                base_audit=base_audit,
                                compare_audit=competitor_audit,
                                token=token
                            )
                            comparison_report['ai_analysis'] = ai_analysis
                        except Exception as e:
                            print(f"⚠️ Error en IA para {competitor_webpage.url}: {e}")
                            comparison_report['ai_analysis'] = None

                    comparisons.append(comparison_report)
                    competitors_audit.append(competitor_audit)

                except Exception as e:
                    print(f"❌ Error procesando competidor {competitor_id}: {e}")
                    continue

        if not comparisons:
            raise Exception("No se pudieron generar comparaciones")

        # Generar resumen general
        overall_summary = _generate_overall_summary(base_audit, comparisons)

        # Generar comparación de schemas con IA
        ai_schema_comparison = await comparator.generate_ai_schema_comparison(
            base_audit=base_audit,
            compare_audits=competitors_audit,
            token=token,
            base_url=base_webpage.url
        )

        # Extract base schemas for report
        base_schemas = []
        if base_audit.seo_analysis and 'schema_markup' in base_audit.seo_analysis:
            base_schemas = base_audit.seo_analysis['schema_markup']

        # Construir resultado final
        comparison_result = {
            "base_url": base_webpage.url,
            "comparisons": comparisons,
            "overall_summary": overall_summary,
            "ai_schema_comparison": ai_schema_comparison,
            "raw_schemas": {"base": base_schemas}
        }

        # Generar reporte
        from app.schemas import audit_schemas
        response_obj = audit_schemas.AuditComparisonResponse(**comparison_result)
        report = ReportGenerator(audit=base_audit).generate_comparison_reports(response_obj)
        print(f"📄 Reporte de comparación generado: {report}")

        # Guardar resultado
        with db_manager.sync_session_context() as session:
            comparison = session.get(AuditComparison, comparison_id)
            if comparison:
                comparison.status = ComparisonStatus.COMPLETED
                comparison.comparison_result = comparison_result
                comparison.completed_at = datetime.now(timezone.utc)

                # Guardar rutas de los reportes generados
                comparison.report_pdf_path = report.get('pdf_path')
                comparison.report_excel_path = report.get('xlsx_path')
                comparison.report_word_path = report.get('word_path')

                session.add(comparison)

        print(f"✅ Comparación completada: {comparison_id}")

    except Exception as e:
        print(f"❌ Error en comparación {comparison_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Guardar estado de error
        try:
            with db_manager.sync_session_context() as session:
                if comparison is None:
                    comparison = session.get(AuditComparison, comparison_id)

                if comparison:
                    comparison.status = ComparisonStatus.FAILED
                    comparison.error_message = str(e)
                    comparison.completed_at = datetime.now(timezone.utc)
                    session.add(comparison)
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo: {inner_error}")


def _generate_overall_summary(base_audit: AuditReport, comparisons: list) -> dict:
    """Generar resumen consolidado de comparaciones"""
    all_performance_scores = [base_audit.performance_score or 0]
    all_seo_scores = [base_audit.seo_score or 0]
    all_accessibility_scores = [base_audit.accessibility_score or 0]
    all_lcp_values = [base_audit.lcp or 0]
    all_cls_values = [base_audit.cls or 0]

    for comp in comparisons:
        perf = comp.get('performance', {}).get('scores', {})
        all_performance_scores.append(perf.get('compare', {}).get('performance_score', 0))
        all_seo_scores.append(perf.get('compare', {}).get('seo_score', 0))
        all_accessibility_scores.append(perf.get('compare', {}).get('accessibility_score', 0))

        cwv = comp.get('performance', {}).get('core_web_vitals', {})
        all_lcp_values.append(cwv.get('compare', {}).get('lcp', 0))
        all_cls_values.append(cwv.get('compare', {}).get('cls', 0))

    base_perf = base_audit.performance_score or 0
    base_seo = base_audit.seo_score or 0

    perf_rank = sum(1 for score in all_performance_scores if score > base_perf) + 1
    seo_rank = sum(1 for score in all_seo_scores if score > base_seo) + 1

    areas_to_improve = []
    if perf_rank > 1:
        areas_to_improve.append("performance")
    if seo_rank > 1:
        areas_to_improve.append("seo")

    all_recommendations = []
    seen_categories = set()
    for comp in comparisons:
        for rec in comp.get('recommendations', []):
            category = rec.get('category', '')
            if category not in seen_categories:
                all_recommendations.append(rec)
                seen_categories.add(category)

    return {
        "total_competitors": len(comparisons),
        "performance_rank": f"{perf_rank}/{len(all_performance_scores)}",
        "seo_rank": f"{seo_rank}/{len(all_seo_scores)}",
        "is_best_performance": perf_rank == 1,
        "is_best_seo": seo_rank == 1,
        "areas_to_improve": areas_to_improve,
        "top_recommendations": all_recommendations[:5],
        "competitive_advantage": {
            "performance_above_average": base_perf > (sum(all_performance_scores) / len(all_performance_scores)),
            "seo_above_average": base_seo > (sum(all_seo_scores) / len(all_seo_scores)),
        }
    }

