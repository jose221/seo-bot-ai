"""
Endpoints para gestión de Auditorías.
Permite iniciar análisis y consultar resultados.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import joinedload
from sqlmodel import select, desc
from sqlalchemy import String, cast as sql_cast, func, or_
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_session
from app.api.deps import get_current_user
from app.helpers import extract_domain
from app.models import AuditComparison
from app.models.user import User
from app.models.webpage import WebPage
from app.models.audit import AuditReport, AuditStatus
from app.models.audit_comparison import ComparisonStatus
from app.schemas import audit_schemas
from app.services.audit_engine import get_audit_engine
from app.services.ai_client import get_ai_client
from app.services.cache import Cache
from app.services.report_generator import ReportGenerator
from app.services.seo_analyzer import SEOAnalyzer
from app.services.audit_comparator import get_audit_comparator
from app.services.background_tasks import run_comparison_task

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
        req_lighthouse_params = dict(
            url=webpage.url,
            instructions=webpage.instructions,
            manual_html_content=webpage.manual_html_content
        )
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


@router.get("/audits/search", response_model=audit_schemas.AuditSearchResponse)
async def search_audits(
        query: Optional[str] = Query(None, description="Buscar por URL o nombre del target"),
        status_filter: Optional[AuditStatus] = Query(None, description="Filtrar por estado"),
        min_performance_score: Optional[float] = Query(None, ge=0, le=100, description="Score mínimo de performance"),
        min_seo_score: Optional[float] = Query(None, ge=0, le=100, description="Score mínimo de SEO"),
        unique_web_page: bool = Query(False, description="Si es True, devuelve solo la auditoría más reciente por web_page_id"),
        exclude_web_page_id: Optional[UUID] = Query(None, description="Excluir auditorías de este web_page_id"),
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Buscar auditorías del usuario autenticado.
    Permite filtrar por URL/nombre del target, estado y scores mínimos.
    Soporta paginación.
    """
    from sqlalchemy import func, or_

    # Solo seleccionar las columnas necesarias para la búsqueda
    statement = select(
        AuditReport.id,
        AuditReport.web_page_id,
        AuditReport.status,
        AuditReport.performance_score,
        AuditReport.seo_score,
        AuditReport.accessibility_score,
        AuditReport.best_practices_score,
        AuditReport.created_at,
        AuditReport.completed_at,
        AuditReport.report_pdf_path,
        AuditReport.report_excel_path,
        WebPage.url.label('web_page_url'),
        WebPage.name.label('web_page_name')
    ).join(WebPage, AuditReport.web_page_id == WebPage.id).where(
        AuditReport.user_id == current_user.id
    )

    # Aplicar filtros
    if query:
        statement = statement.where(
            or_(
                WebPage.url.ilike(f"%{query}%"),
                WebPage.name.ilike(f"%{query}%")
            )
        )

    if status_filter:
        statement = statement.where(sql_cast(AuditReport.status, String) == status_filter.value)

    if min_performance_score is not None:
        statement = statement.where(AuditReport.performance_score >= min_performance_score)

    if min_seo_score is not None:
        statement = statement.where(AuditReport.seo_score >= min_seo_score)

    # Excluir web_page_id específico
    if exclude_web_page_id is not None:
        statement = statement.where(AuditReport.web_page_id != exclude_web_page_id)

    statement = statement.order_by(desc(AuditReport.created_at))

    # Contar total
    count_statement = select(func.count()).select_from(AuditReport).join(
        WebPage, AuditReport.web_page_id == WebPage.id
    ).where(AuditReport.user_id == current_user.id)

    if query:
        count_statement = count_statement.where(
            or_(
                WebPage.url.ilike(f"%{query}%"),
                WebPage.name.ilike(f"%{query}%")
            )
        )

    if status_filter:
        count_statement = count_statement.where(sql_cast(AuditReport.status, String) == status_filter.value)

    if min_performance_score is not None:
        count_statement = count_statement.where(AuditReport.performance_score >= min_performance_score)

    if min_seo_score is not None:
        count_statement = count_statement.where(AuditReport.seo_score >= min_seo_score)

    if exclude_web_page_id is not None:
        count_statement = count_statement.where(AuditReport.web_page_id != exclude_web_page_id)

    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    audits = result.all()

    # Si unique_web_page=True, filtrar para obtener solo la más reciente por web_page_id
    if unique_web_page:
        # Crear diccionario para almacenar solo la auditoría más reciente por web_page_id
        unique_audits_dict = {}
        for audit in audits:
            web_page_id = audit.web_page_id
            # Si no existe o la actual es más reciente, reemplazar
            if web_page_id not in unique_audits_dict or audit.created_at > unique_audits_dict[web_page_id].created_at:
                unique_audits_dict[web_page_id] = audit

        # Convertir de vuelta a lista
        audits = list(unique_audits_dict.values())
        # Actualizar el total
        total = len(audits)

    # Verificar reportes faltantes también en búsqueda
    audits_modified = False
    # audits es lista de Row (si no seleccionamos scalars) o lista de objetos.
    # En search_audits seleccionamos columnas especificas asi que 'audits' es lista de Rows/Tuples, NO objetos ORM attached a session completos de la misma manera
    # Wait, 'statement' en search_audits hace select de columnas especificas: select(AuditReport.id, ...).
    # Entonces 'audits' son named tuples. No podemos hacer session.add(audit).
    # Tendriamos que cargar los objetos completos o hacer update.
    # Dado que search es más light, y devolvemos un esquema simplificado AuditSearchItem,
    # tal vez NO deberiamos regenerar aqui para no matar performance en busquedas rapidas.
    # Pero el usuario pidio "getALL y el find". search es un find? Probablemente 'list_audits' es el getAll.
    # search_audits devuelve AuditSearchItem. list_audits devuelve AuditResponse.
    # El usuario dijo "getALL y find". Asumire list_audits y get_audit.
    # En search solo devolveremos lo que hay.

    return audit_schemas.AuditSearchResponse(
        items=[
            audit_schemas.AuditSearchItem(
                id=a.id,
                web_page_id=a.web_page_id,
                status=a.status,
                performance_score=a.performance_score,
                seo_score=a.seo_score,
                accessibility_score=a.accessibility_score,
                best_practices_score=a.best_practices_score,
                created_at=a.created_at,
                completed_at=a.completed_at,
                web_page_url=a.web_page_url,
                web_page_name=a.web_page_name,
                report_pdf_path=a.report_pdf_path,
                report_excel_path=a.report_excel_path
            )
            for a in audits
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/audits/comparisons", response_model=audit_schemas.ComparisonListResponse)
async def list_comparisons(
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Listar comparaciones del usuario con paginación.
    """
    # Query base
    statement = select(
        AuditComparison.id,
        AuditComparison.base_web_page_id,
        AuditComparison.status,
        AuditComparison.created_at,
        AuditComparison.completed_at,
        AuditComparison.error_message,
        AuditComparison.comparison_result,
        AuditComparison.report_pdf_path,
        AuditComparison.report_excel_path,
        AuditComparison.report_word_path
    ).where(
        AuditComparison.user_id == current_user.id
    ).order_by(desc(AuditComparison.created_at))

    # Contar total
    count_statement = select(func.count()).select_from(AuditComparison).where(
        AuditComparison.user_id == current_user.id
    )
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    comparisons = result.all()

    # Construir items de respuesta
    items = []
    for comp in comparisons:
        base_url = None
        total_competitors = None

        if comp.comparison_result:
            base_url = comp.comparison_result.get('base_url')
            total_competitors = len(comp.comparison_result.get('comparisons', []))

        items.append(audit_schemas.ComparisonListItem(
            id=comp.id,
            base_web_page_id=comp.base_web_page_id,
            status=comp.status,
            created_at=comp.created_at,
            completed_at=comp.completed_at,
            base_url=base_url,
            total_competitors=total_competitors,
            error_message=comp.error_message,
            report_pdf_path=comp.report_pdf_path,
            report_excel_path=comp.report_excel_path,
            report_word_path=comp.report_word_path
        ))

    return audit_schemas.ComparisonListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/audits/comparisons/{comparison_id}", response_model=audit_schemas.ComparisonDetailResponse)
async def get_comparison(
        comparison_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """
    Obtener detalles de una comparación específica.
    """
    statement = select(AuditComparison).where(
        AuditComparison.id == comparison_id,
        AuditComparison.user_id == current_user.id
    )
    result = await session.execute(statement)
    comparison = result.scalars().first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparación no encontrada"
        )

    # Asegurar que se carguen los datos más recientes
    await session.refresh(comparison)

    # Verificar y generar reportes si faltan (On-demand)
    if comparison.status == ComparisonStatus.COMPLETED and (not comparison.report_pdf_path or not comparison.report_excel_path or not comparison.report_word_path):
        try:
            print(f"🔄 Generando reportes faltantes para comparison {comparison.id}")
            # Reconstruir objeto de respuesta para el generador
            comparison_data = audit_schemas.AuditComparisonResponse(**comparison.comparison_result)

            # Obtener audit base para inicializar generador (necesita base_audit para paths)
            base_audit_stmt = select(AuditReport).where(
                AuditReport.web_page_id == comparison.base_web_page_id,
                sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
            ).order_by(desc(AuditReport.created_at)).limit(1)

            result_audit = await session.execute(base_audit_stmt)
            base_audit = result_audit.scalars().first()

            if base_audit:
                 report_paths = ReportGenerator(audit=base_audit).generate_comparison_reports(comparison_data)
                 comparison.report_pdf_path = report_paths.get('pdf_path')
                 comparison.report_excel_path = report_paths.get('xlsx_path')
                 comparison.report_word_path = report_paths.get('word_path')

                 session.add(comparison)
                 await session.commit()
                 await session.refresh(comparison)
            else:
                 print(f"⚠️ No se encontró audit base para regenerar reportes de comparación {comparison.id}")

        except Exception as e:
            print(f"⚠️ Error generando reportes on-demand para comparison: {e}")
            import traceback
            traceback.print_exc()

    # Construir respuesta
    comparison_result = None
    if comparison.comparison_result and comparison.status == ComparisonStatus.COMPLETED:
        comparison_result = audit_schemas.AuditComparisonResponse(**comparison.comparison_result)

    return audit_schemas.ComparisonDetailResponse(
        id=comparison.id,
        base_web_page_id=comparison.base_web_page_id,
        status=comparison.status,
        created_at=comparison.created_at,
        completed_at=comparison.completed_at,
        comparison_result=comparison_result,
        error_message=comparison.error_message,
        report_pdf_path=comparison.report_pdf_path,
        report_excel_path=comparison.report_excel_path,
        report_word_path=comparison.report_word_path
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
    ).options(joinedload(AuditReport.web_page))
    result = await session.execute(statement)
    audit = result.scalars().first()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )

    # Verificar y generar reportes si faltan
    if audit.status == AuditStatus.COMPLETED and (not audit.report_pdf_path or not audit.report_excel_path or not audit.report_word_path):
        try:
            print(f"🔄 Generando reportes faltantes para audit {audit.id}")
            report_paths = ReportGenerator(audit=audit).generate_all()
            audit.report_pdf_path = report_paths.get('pdf_path')
            audit.report_excel_path = report_paths.get('xlsx_path')
            audit.report_word_path = report_paths.get('word_path')

            session.add(audit)
            await session.commit()
            await session.refresh(audit)
        except Exception as e:
            print(f"⚠️ Error generando reportes on-demand: {e}")

    return audit


@router.get("/audits", response_model=audit_schemas.AuditListResponse)
async def list_audits(
        web_page_id: Optional[UUID] = Query(None, description="Filtrar por target"),
        status_filter: Optional[AuditStatus] = Query(None, description="Filtrar por estado"),
        page: int = Query(1, ge=1),
        page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
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

    statement = statement.options(joinedload(AuditReport.web_page)).order_by(desc(AuditReport.created_at))

    # Contar total
    count_result = await session.execute(statement)
    total = len(count_result.unique().scalars().all())

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    audits = result.unique().scalars().all()

    # Verificar reportes faltantes para los items devueltos (solo si status=completed)
    # Esto asegura que el frontend reciba URLs válidas aunque sea la primera vez que se piden
    audits_modified = False
    for audit in audits:
        if audit.status == AuditStatus.COMPLETED and (not audit.report_pdf_path or not audit.report_excel_path or not audit.report_word_path):
            try:
                # Generar reportes
                # Nota: Esto es bloqueante, pero necesario para cumplir requerimiento de devolver URLs
                # Para paginación grande esto podría ser lento la primera vez
                report_paths = ReportGenerator(audit=audit).generate_all()
                audit.report_pdf_path = report_paths.get('pdf_path')
                audit.report_excel_path = report_paths.get('xlsx_path')
                audit.report_word_path = report_paths.get('word_path')
                session.add(audit)
                audits_modified = True
            except Exception as e:
                print(f"⚠️ Error generando reportes en listado para audit {audit.id}: {e}")

    if audits_modified:
        # Hacer commit si se generaron reportes para algún audit
        await session.commit()

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


@router.post("/audits/compare", response_model=audit_schemas.ComparisonTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def audits_compare(
        audit_request: audit_schemas.AuditCompare,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
        token: str = Depends(lambda: None)
):
    """
    Comparar una página base contra múltiples competidores.
    La comparación se ejecuta en segundo plano.
    """
    # Verificar que la página base existe y pertenece al usuario
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

    # Verificar que existe una auditoría completada para la página base
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

    # Crear registro de comparación
    comparison = AuditComparison(
        base_web_page_id=audit_request.web_page_id,
        user_id=current_user.id,
        competitor_web_page_ids=[str(id) for id in audit_request.web_page_id_to_compare],
        include_ai_analysis=audit_request.include_ai_analysis,
        status=ComparisonStatus.PENDING
    )

    session.add(comparison)
    await session.commit()
    await session.refresh(comparison)

    # Obtener token del contexto
    auth_token = getattr(current_user, '_token', None) or "dummy-token"

    # Lanzar tarea en segundo plano
    background_tasks.add_task(
        run_comparison_task,
        comparison_id=comparison.id,
        base_web_page_id=audit_request.web_page_id,
        competitor_ids=audit_request.web_page_id_to_compare,
        include_ai=audit_request.include_ai_analysis,
        token=auth_token,
        user_id=current_user.id
    )

    return audit_schemas.ComparisonTaskResponse(
        task_id=comparison.id,
        status=comparison.status,
        message=f"Comparación iniciada para {base_webpage.url} vs {len(audit_request.web_page_id_to_compare)} competidores"
    )

