"""
Endpoints para gestión de Auditorías.
Permite iniciar análisis y consultar resultados.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlmodel import select, desc
from sqlalchemy import String, cast as sql_cast
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_session
from app.api.deps import get_current_user
from app.helpers import extract_domain
from app.models.user import User
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.schemas import audit_schemas
from app.services.audit_engine import get_audit_engine
from app.services.ai_client import get_ai_client
from app.services.cache import Cache
from app.services.report_generator import ReportGenerator
from app.services.seo_analyzer import SEOAnalyzer
from app.services.audit_comparator import get_audit_comparator

router = APIRouter()


async def run_audit_task(
        audit_id: UUID,
        webpage: WebPage,
        include_ai: bool,
        token: str
):
    """
    Tarea en segundo plano para ejecutar auditoría.
    Se ejecuta de forma asíncrona sin bloquear la respuesta.
    """
    from app.core.database import db_manager

    audit = None  # Inicializar para evitar UnboundLocalError
    _cache = Cache(table_name="audits_reports")
    try:
        # Usar el context manager síncrono del gestor de BD
        with db_manager.sync_session_context() as session:
            # Obtener el audit report
            audit = session.get(AuditReport, audit_id)
            if not audit:
                print(f"❌ No se encontró audit {audit_id}")
                return

            # Actualizar estado
            audit.status = AuditStatus.IN_PROGRESS
            session.add(audit)
            # No llamar commit aquí, el context manager lo hace automáticamente

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

        # Si se solicita análisis de IA
        ai_analysis_data = None

        if include_ai:
            print(f"🤖 Ejecutando análisis de IA...")
            ai_client = get_ai_client()

            try:
                req_ai_analysis_params = dict(
                    url=webpage.url,
                )
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

        _seo_analyzer = SEOAnalyzer(url=extract_domain(webpage.url),
                                    html_content=lighthouse_result.get('html_content_raw', ''))
        seo_analysis = _seo_analyzer.run_full_analysis()

        # Actualizar resultados en la base de datos
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
            #eliminar html y htl_raw
            lighthouse_result.pop('html_content', None)
            lighthouse_result.pop('html_content_raw', None)
            if audit:
                # Extraer métricas
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

                #genera el reporte
                report = ReportGenerator(audit=audit).generate_all()
                print(report)
                #audit.report_path = report.get('pdf_path')
                #audit.excel_path = report.get('xlsx_path')

                session.add(audit)
                # No llamar commit aquí, el context manager lo hace automáticamente

        print(f"✅ Auditoría completada: {audit_id}")

    except Exception as e:
        print(f"❌ Error en auditoría {audit_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Intentar actualizar el audit con el error
        try:
            with db_manager.sync_session_context() as session:
                if audit is None:
                    audit = session.get(AuditReport, audit_id)

                if audit:
                    audit.status = AuditStatus.FAILED
                    audit.error_message = str(e)
                    audit.completed_at = datetime.now(timezone.utc)
                    session.add(audit)
                    # No llamar commit aquí, el context manager lo hace automáticamente
        except Exception as inner_error:
            print(f"❌ Error al guardar estado de fallo: {inner_error}")


@router.post("/audits", response_model=audit_schemas.AuditTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_audit(
        audit_request: audit_schemas.AuditCreate,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
        token: str = Depends(lambda: None)  # Se obtendrá del header en deps
):
    """
    Iniciar una nueva auditoría para un target.
    La auditoría se ejecuta en segundo plano.
    """
    # Verificar que el target existe y pertenece al usuario
    statement = select(WebPage).where(
        WebPage.id == audit_request.web_page_id,
        WebPage.user_id == current_user.id,
        WebPage.is_active == True
    )
    result = await session.execute(statement)
    webpage = result.scalars().first()

    if not webpage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target no encontrado o no tienes acceso"
        )

    # Crear registro de auditoría
    audit = AuditReport(
        web_page_id=webpage.id,
        user_id=current_user.id,
        status=AuditStatus.PENDING
    )

    session.add(audit)
    await session.commit()
    await session.refresh(audit)

    # Obtener token del contexto (se pasa desde deps)
    auth_token = getattr(current_user, '_token', None) or "dummy-token"

    # Lanzar tarea en segundo plano
    background_tasks.add_task(
        run_audit_task,
        audit_id=audit.id,
        webpage=webpage,
        include_ai=audit_request.include_ai_analysis,
        token=auth_token
    )

    return audit_schemas.AuditTaskResponse(
        task_id=audit.id,
        status=audit.status,
        message=f"Auditoría iniciada para {webpage.url}"
    )


@router.get("/audits/{audit_id}", response_model=audit_schemas.AuditResponse)
async def get_audit(
        audit_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Obtener detalles de una auditoría específica.
    """
    statement = select(AuditReport).where(
        AuditReport.id == audit_id,
        AuditReport.user_id == current_user.id
    )
    result = await session.execute(statement)
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )

    return audit


@router.get("/audits", response_model=audit_schemas.AuditListResponse)
async def list_audits(
        web_page_id: Optional[UUID] = Query(None, description="Filtrar por target"),
        status_filter: Optional[AuditStatus] = Query(None, description="Filtrar por estado"),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Listar auditorías del usuario con filtros opcionales.
    """
    # Query base
    statement = select(AuditReport).where(
        AuditReport.user_id == current_user.id
    )

    # Aplicar filtros
    if web_page_id:
        statement = statement.where(AuditReport.web_page_id == web_page_id)
    if status_filter:
        statement = statement.where(sql_cast(AuditReport.status, String) == status_filter.value)

    statement = statement.order_by(desc(AuditReport.created_at))

    # Contar total
    count_result = await session.execute(statement)
    total = len(count_result.scalars().all())

    # Paginación
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    audits = result.scalars().all()

    return audit_schemas.AuditListResponse(
        items=[audit_schemas.AuditResponse.model_validate(a) for a in audits],
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/audits/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
        audit_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Eliminar una auditoría.
    """
    statement = select(AuditReport).where(
        AuditReport.id == audit_id,
        AuditReport.user_id == current_user.id
    )
    result = await session.execute(statement)
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )

    await session.delete(audit)
    await session.commit()

    return None


@router.post("/audits/compare", response_model=audit_schemas.AuditComparisonResponse, status_code=status.HTTP_200_OK)
async def audits_compare(
        audit_request: audit_schemas.AuditCompare,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
        token: str = Depends(lambda: None)
):
    """
    Comparar una página base contra múltiples competidores.

    Compara:
    - Schemas estructurados (JSON-LD)
    - Métricas de rendimiento (Lighthouse)
    - Core Web Vitals
    - SEO on-page
    - Genera recomendaciones accionables basadas en todas las comparaciones
    """
    # Obtener página base
    statement = select(WebPage).where(
        WebPage.id == audit_request.web_page_id,
        WebPage.user_id == current_user.id,
        WebPage.is_active == True
    )
    result = await session.execute(statement)
    base_webpage = result.scalars().first()

    if not base_webpage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target base no encontrado o no tienes acceso"
        )

    # Obtener auditoría completada de la página base
    base_audit_stmt = select(AuditReport).where(
        AuditReport.web_page_id == base_webpage.id,
        sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
    ).order_by(desc(AuditReport.created_at)).limit(1)

    base_audit_result = await session.execute(base_audit_stmt)
    base_audit = base_audit_result.scalars().first()

    if not base_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay auditorías completadas para la página base {base_webpage.url}"
        )

    # Inicializar estructuras para resultados
    comparisons = []
    auth_token = getattr(current_user, '_token', None) or "dummy-token"
    _cache = Cache(table_name="audits_reports_compare_")
    comparator = get_audit_comparator()

    competitors_audit = []
    # Procesar cada competidor
    for competitor_id in audit_request.web_page_id_to_compare:
        try:
            # Obtener página competidora
            competitor_stmt = select(WebPage).where(
                WebPage.id == competitor_id,
                WebPage.user_id == current_user.id,
                WebPage.is_active == True
            )
            competitor_result = await session.execute(competitor_stmt)
            competitor_webpage = competitor_result.scalars().first()

            if not competitor_webpage:
                print(f"⚠️  Target {competitor_id} no encontrado, se omitirá")
                continue

            # Obtener auditoría completada del competidor
            competitor_audit_stmt = select(AuditReport).where(
                AuditReport.web_page_id == competitor_webpage.id,
                sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
            ).order_by(desc(AuditReport.created_at)).limit(1)

            competitor_audit_result = await session.execute(competitor_audit_stmt)
            competitor_audit = competitor_audit_result.scalars().first()

            if not competitor_audit:
                print(f"⚠️  No hay auditoría completada para {competitor_webpage.url}, se omitirá")
                continue

            # Generar comparación individual
            comparison_report = comparator.generate_comparison_report(
                base_audit=base_audit,
                compare_audit=competitor_audit,
                base_url=base_webpage.url,
                compare_url=competitor_webpage.url
            )

            # Generar análisis de IA si se solicita
            if audit_request.include_ai_analysis and auth_token:
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
                        token=auth_token
                    )
                    comparison_report['ai_analysis'] = ai_analysis
                except Exception as e:
                    print(f"⚠️ Error generando análisis de IA para {competitor_webpage.url}: {e}")
                    comparison_report['ai_analysis'] = None

            # Agregar resultado a la lista
            comparisons.append(audit_schemas.SingleComparisonResult(
                compare_url=comparison_report['compare_url'],
                comparison_date=comparison_report.get('comparison_date'),
                summary=comparison_report['summary'],
                performance=comparison_report['performance'],
                schemas=comparison_report['schemas'],
                seo_analysis=comparison_report['seo_analysis'],
                recommendations=comparison_report['recommendations'],
                ai_analysis=comparison_report.get('ai_analysis')
            ))
            competitors_audit.append(competitor_audit)

        except Exception as e:
            print(f"❌ Error procesando competidor {competitor_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    if not comparisons:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo generar ninguna comparación. Verifica que los competidores tengan auditorías completadas."
        )

    # Generar resumen general consolidado
    overall_summary = _generate_overall_summary(base_audit, comparisons)
    response_generate_ai_schema_comparison = await comparator.generate_ai_schema_comparison(
        base_audit=base_audit,
        compare_audits=competitors_audit,
        token=auth_token
    )
    response_f = audit_schemas.AuditComparisonResponse(
        base_url=base_webpage.url,
        comparisons=comparisons,
        overall_summary=overall_summary,
        ai_schema_comparison=response_generate_ai_schema_comparison
    )
    report = ReportGenerator(audit=base_audit).generate_comparison_reports(response_f)
    print(report)
    return response_f

def _generate_overall_summary(base_audit: AuditReport, comparisons: list) -> Dict[str, Any]:
    """
    Genera un resumen consolidado comparando contra todos los competidores.
    """
    # Recopilar todas las métricas
    all_performance_scores = [base_audit.performance_score or 0]
    all_seo_scores = [base_audit.seo_score or 0]
    all_accessibility_scores = [base_audit.accessibility_score or 0]
    all_lcp_values = [base_audit.lcp or 0]
    all_cls_values = [base_audit.cls or 0]

    for comp in comparisons:
        perf = comp.performance.scores
        all_performance_scores.append(perf.get('compare', {}).get('performance_score', 0))
        all_seo_scores.append(perf.get('compare', {}).get('seo_score', 0))
        all_accessibility_scores.append(perf.get('compare', {}).get('accessibility_score', 0))

        cwv = comp.performance.core_web_vitals
        all_lcp_values.append(cwv.get('compare', {}).get('lcp', 0))
        all_cls_values.append(cwv.get('compare', {}).get('cls', 0))

    # Calcular posición relativa
    base_perf = base_audit.performance_score or 0
    base_seo = base_audit.seo_score or 0

    perf_rank = sum(1 for score in all_performance_scores if score > base_perf) + 1
    seo_rank = sum(1 for score in all_seo_scores if score > base_seo) + 1

    # Identificar áreas de mejora
    areas_to_improve = []
    if perf_rank > 1:
        areas_to_improve.append("performance")
    if seo_rank > 1:
        areas_to_improve.append("seo")

    # Recopilar todas las recomendaciones únicas
    all_recommendations = []
    seen_categories = set()
    for comp in comparisons:
        for rec in comp.recommendations:
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
        "top_recommendations": all_recommendations[:5],  # Top 5 recomendaciones
        "competitive_advantage": {
            "performance_above_average": base_perf > (sum(all_performance_scores) / len(all_performance_scores)),
            "seo_above_average": base_seo > (sum(all_seo_scores) / len(all_seo_scores)),
        }
    }

