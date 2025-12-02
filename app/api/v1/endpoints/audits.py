"""
Endpoints para gestión de Auditorías.
Permite iniciar análisis y consultar resultados.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlmodel import select, desc
from typing import Optional
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
            prefix="lighthouse_report",
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
                    prefix="ai_analysis",
                    ttl=3600,
                    callback_async=ai_client.analyze_seo_content,
                    html_content=lighthouse_result.get('html_content', ''),
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
                                    html_content=lighthouse_result.get('html_content', ''))
        seo_analysis = _seo_analyzer.run_full_analysis()

        # Actualizar resultados en la base de datos
        with db_manager.sync_session_context() as session:
            audit = session.get(AuditReport, audit_id)
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
        statement = statement.where(AuditReport.status == status_filter)

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
    Comparar dos auditorías SEO y generar reporte estructurado.

    Compara:
    - Schemas estructurados (JSON-LD)
    - Métricas de rendimiento (Lighthouse)
    - Core Web Vitals
    - SEO on-page
    - Genera recomendaciones accionables
    """
    # Obtener página base
    statement = select(WebPage).where(
        WebPage.id == audit_request.web_page_id,
        WebPage.user_id == current_user.id,
        WebPage.is_active == True
    )
    result = await session.execute(statement)
    webpage = result.scalars().first()

    # Obtener página a comparar
    statement_to_compare = select(WebPage).where(
        WebPage.id == audit_request.web_page_id_to_compare,
        WebPage.user_id == current_user.id,
        WebPage.is_active == True
    )
    result = await session.execute(statement_to_compare)
    webpage_to_compare = result.scalars().first()

    if not webpage or not webpage_to_compare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target no encontrado o no tienes acceso"
        )

    # Obtener última auditoría completada de cada página
    base_audit_stmt = select(AuditReport).where(
        AuditReport.web_page_id == webpage.id,
        AuditReport.status == AuditStatus.COMPLETED
    ).order_by(desc(AuditReport.created_at)).limit(1)

    base_audit_result = await session.execute(base_audit_stmt)
    base_audit = base_audit_result.scalars().first()

    compare_audit_stmt = select(AuditReport).where(
        AuditReport.web_page_id == webpage_to_compare.id,
        AuditReport.status == AuditStatus.COMPLETED
    ).order_by(desc(AuditReport.created_at)).limit(1)

    compare_audit_result = await session.execute(compare_audit_stmt)
    compare_audit = compare_audit_result.scalars().first()

    if not base_audit or not compare_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay auditorías completadas para comparar. Ejecuta auditorías primero."
        )

    # Generar comparación estructurada
    comparator = get_audit_comparator()
    comparison_report = comparator.generate_comparison_report(
        base_audit=base_audit,
        compare_audit=compare_audit,
        base_url=webpage.url,
        compare_url=webpage_to_compare.url
    )

    # Generar análisis de IA si se solicita
    if audit_request.include_ai_analysis and token:
        try:
            ai_analysis = await comparator.generate_ai_comparison(
                base_audit=base_audit,
                compare_audit=compare_audit,
                base_url=webpage.url,
                compare_url=webpage_to_compare.url,
                token=token
            )
            comparison_report['ai_analysis'] = ai_analysis
        except Exception as e:
            print(f"⚠️ Error generando análisis de IA: {e}")
            comparison_report['ai_analysis'] = None

    return audit_schemas.AuditComparisonResponse(**comparison_report)

