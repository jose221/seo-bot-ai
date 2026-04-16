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
from datetime import datetime

from app.core.database import get_session
from app.api.deps import get_current_user
from app.helpers import extract_domain
from app.models import AuditComparison, AuditSchemaReview, SchemaAuditStatus, SchemaAuditSourceType
from app.models import AuditUrlValidation, UrlValidationStatus, UrlValidationSourceType
from app.models.url_validation_comment import UrlValidationComment, CommentStatus
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
from app.services.schema_audit_service import get_schema_audit_service
from app.services.url_validation_service import get_url_validation_service
from app.services.background_tasks import run_comparison_task, run_schema_audit_task, run_url_validation_task, run_url_validation_single_url_task

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

                # Extraer métricas de uso y contenido
                usage = ai_analysis.get('usage', {})
                content = ai_analysis.get('content', '')

                ai_analysis_data = {
                    'content': content,
                    'usage': usage,
                    'generated_at': datetime.utcnow().isoformat(),
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

                # Asignar datos de IA y guardar tokens
                if ai_analysis_data:
                    audit.ai_suggestions = ai_analysis_data
                    # Guardar tokens en columnas dedicadas si existen en ai_analysis_data
                    if 'usage' in ai_analysis_data:
                        usage_data = ai_analysis_data['usage']
                        audit.input_tokens = usage_data.get('prompt_tokens', 0)
                        audit.output_tokens = usage_data.get('completion_tokens', 0)

                audit.status = AuditStatus.COMPLETED
                audit.completed_at = datetime.utcnow()
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
                    audit.completed_at = datetime.utcnow()
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
    Solo columnas necesarias para la tabla (sin comparison_result JSONB enorme).
    La URL de la página base se obtiene via JOIN con web_pages.
    El total de competidores se obtiene de competitor_web_page_ids (array ligero).
    """
    # Contar total
    count_statement = select(func.count()).select_from(AuditComparison).where(
        AuditComparison.user_id == current_user.id
    )
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Solo columnas necesarias + URL de web_page via JOIN (sin comparison_result pesado)
    statement = select(
        AuditComparison.id,
        AuditComparison.base_web_page_id,
        AuditComparison.status,
        AuditComparison.created_at,
        AuditComparison.completed_at,
        AuditComparison.error_message,
        AuditComparison.competitor_web_page_ids,  # array ligero para contar competidores
        AuditComparison.report_pdf_path,
        AuditComparison.report_excel_path,
        AuditComparison.report_word_path,
        AuditComparison.proposal_report_pdf_path,
        AuditComparison.proposal_report_word_path,
        WebPage.url.label("base_url"),
    ).join(WebPage, AuditComparison.base_web_page_id == WebPage.id, isouter=True).where(
        AuditComparison.user_id == current_user.id
    ).order_by(desc(AuditComparison.created_at))

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    comparisons = result.all()

    items = [
        audit_schemas.ComparisonListItem(
            id=comp.id,
            base_web_page_id=comp.base_web_page_id,
            status=comp.status,
            created_at=comp.created_at,
            completed_at=comp.completed_at,
            base_url=comp.base_url,
            total_competitors=len(comp.competitor_web_page_ids) if comp.competitor_web_page_ids else 0,
            error_message=comp.error_message,
            report_pdf_path=comp.report_pdf_path,
            report_excel_path=comp.report_excel_path,
            report_word_path=comp.report_word_path,
            proposal_report_pdf_path=comp.proposal_report_pdf_path,
            proposal_report_word_path=comp.proposal_report_word_path,
        )
        for comp in comparisons
    ]

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
        report_word_path=comparison.report_word_path,
        proposal_report_pdf_path=comparison.proposal_report_pdf_path,
        proposal_report_word_path=comparison.proposal_report_word_path
    )


@router.post("/audits/schemas", response_model=audit_schemas.AuditSchemasTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_schema_audit(
        audit_request: audit_schemas.AuditSchemasCreate,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
        token: str = Depends(lambda: None)
):
    """
    Iniciar una auditoría de schemas (original vs propuesto vs nuevo).
    """
    source_obj = None
    source_web_page_id = None
    proposal_text = None
    schema_audit_service = get_schema_audit_service()

    if audit_request.source_type == "audit_page":
        stmt = select(AuditReport).where(
            AuditReport.id == audit_request.source_id,
            AuditReport.user_id == current_user.id
        )
        source_obj = (await session.execute(stmt)).scalars().first()
        if not source_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit page no encontrado")

        source_web_page_id = source_obj.web_page_id
        ai_suggestions = source_obj.ai_suggestions or {}
        proposal_text = ai_suggestions.get("content") or ai_suggestions.get("analysis")

    elif audit_request.source_type == "audit_comparison":
        stmt = select(AuditComparison).where(
            AuditComparison.id == audit_request.source_id,
            AuditComparison.user_id == current_user.id
        )
        source_obj = (await session.execute(stmt)).scalars().first()
        if not source_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit comparison no encontrado")

        source_web_page_id = source_obj.base_web_page_id
        comparison_result = source_obj.comparison_result or {}
        proposal_text = comparison_result.get("ai_schema_comparison")

    latest_audit_stmt = select(AuditReport).where(
        AuditReport.web_page_id == source_web_page_id,
        AuditReport.user_id == current_user.id,
        sql_cast(AuditReport.status, String) == AuditStatus.COMPLETED.value
    ).order_by(desc(AuditReport.created_at)).limit(1)

    latest_audit = (await session.execute(latest_audit_stmt)).scalars().first()
    if not latest_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró auditoría completada para extraer schema base"
        )

    original_schema = (latest_audit.seo_analysis or {}).get("schema_markup", [])
    proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)

    if proposed_schema is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo extraer el esquema propuesto final desde la propuesta guardada"
        )

    schema_audit = AuditSchemaReview(
        user_id=current_user.id,
        source_type=SchemaAuditSourceType(audit_request.source_type),
        source_id=audit_request.source_id,
        original_schema_json=original_schema,
        proposed_schema_json=proposed_schema,
        incoming_schema_json=audit_request.modified_schema_json,
        include_ai_analysis=audit_request.include_ai_analysis,
        programming_language=audit_request.programming_language,
        status=SchemaAuditStatus.PENDING
    )

    session.add(schema_audit)
    await session.commit()
    await session.refresh(schema_audit)

    auth_token = getattr(current_user, '_token', None) or "dummy-token"

    background_tasks.add_task(
        run_schema_audit_task,
        schema_audit_id=schema_audit.id,
        token=auth_token
    )

    return audit_schemas.AuditSchemasTaskResponse(
        task_id=schema_audit.id,
        status=schema_audit.status,
        message="Auditoría de schemas iniciada"
    )


@router.get("/audits/schemas", response_model=audit_schemas.AuditSchemasListResponse)
async def list_schema_audits(
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """Listar auditorías de schemas del usuario."""
    # Solo columnas necesarias para la tabla (sin JSON/texto pesados)
    statement = select(
        AuditSchemaReview.id,
        AuditSchemaReview.source_type,
        AuditSchemaReview.source_id,
        AuditSchemaReview.status,
        AuditSchemaReview.programming_language,
        AuditSchemaReview.created_at,
        AuditSchemaReview.completed_at,
        AuditSchemaReview.error_message,
        AuditSchemaReview.report_pdf_path,
        AuditSchemaReview.report_word_path,
    ).where(
        AuditSchemaReview.user_id == current_user.id
    ).order_by(desc(AuditSchemaReview.created_at))

    count_statement = select(func.count()).select_from(AuditSchemaReview).where(
        AuditSchemaReview.user_id == current_user.id
    )
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    if page_size is not None:
        statement = statement.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(statement)
    rows = result.all()

    return audit_schemas.AuditSchemasListResponse(
        items=[
            audit_schemas.AuditSchemasListItem(
                id=row.id,
                source_type=row.source_type,
                source_id=row.source_id,
                status=row.status,
                programming_language=row.programming_language,
                created_at=row.created_at,
                completed_at=row.completed_at,
                error_message=row.error_message,
                report_pdf_path=row.report_pdf_path,
                report_word_path=row.report_word_path,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/audits/schemas/{schema_audit_id}", response_model=audit_schemas.AuditSchemasDetailResponse)
async def get_schema_audit(
        schema_audit_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session)
):
    """Obtener detalle de una auditoría de schemas."""
    stmt = select(AuditSchemaReview).where(
        AuditSchemaReview.id == schema_audit_id,
        AuditSchemaReview.user_id == current_user.id
    )
    schema_audit = (await session.execute(stmt)).scalars().first()

    if not schema_audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditoría de schemas no encontrada")

    return audit_schemas.AuditSchemasDetailResponse.model_validate(schema_audit)


# ---------------------------------------------------------------------------
# URL Validations Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/audits/url-validations",
    response_model=audit_schemas.AuditUrlValidationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_url_validation(
        request_body: audit_schemas.AuditUrlValidationCreate,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
        token: str = Depends(lambda: None),
):
    """
    Iniciar validación batch de schemas por URLs.
    Procesa N URLs individualmente en segundo plano.
    """
    # 1. Parsear URLs
    url_service = get_url_validation_service()
    urls = url_service.parse_urls(request_body.urls)

    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron URLs válidas en el campo 'urls'"
        )

    # 2. Resolver source y extraer proposed_schema
    schema_audit_service = get_schema_audit_service()
    proposed_schema = None

    if request_body.source_type == "audit_page":
        stmt = select(AuditReport).where(
            AuditReport.id == request_body.source_id,
            AuditReport.user_id == current_user.id,
        )
        source_obj = (await session.execute(stmt)).scalars().first()
        if not source_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit page no encontrado",
            )
        ai_suggestions = source_obj.ai_suggestions or {}
        proposal_text = ai_suggestions.get("content") or ai_suggestions.get("analysis")
        proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)

        # Fallback: usar schema_markup original si no hay propuesta
        if proposed_schema is None:
            proposed_schema = (source_obj.seo_analysis or {}).get("schema_markup", [])

    elif request_body.source_type == "audit_comparison":
        stmt = select(AuditComparison).where(
            AuditComparison.id == request_body.source_id,
            AuditComparison.user_id == current_user.id,
        )
        source_obj = (await session.execute(stmt)).scalars().first()
        if not source_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit comparison no encontrado",
            )
        comparison_result = source_obj.comparison_result or {}
        proposal_text = comparison_result.get("ai_schema_comparison")
        proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)

        # Fallback: usar raw_schemas del base
        if proposed_schema is None:
            proposed_schema = comparison_result.get("raw_schemas", {}).get("base", [])

    if not proposed_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener un esquema propuesto desde el source indicado",
        )

    # 3. Crear registro
    validation = AuditUrlValidation(
        user_id=current_user.id,
        source_type=UrlValidationSourceType(request_body.source_type),
        source_id=request_body.source_id,
        name_validation=request_body.name_validation,
        description_validation=request_body.description_validation,
        ai_instruction=request_body.ai_instruction,
        urls_raw=request_body.urls,
        status=UrlValidationStatus.PENDING,
    )

    session.add(validation)
    await session.commit()
    await session.refresh(validation)

    # 4. Lanzar tarea en segundo plano
    auth_token = getattr(current_user, "_token", None) or "dummy-token"

    background_tasks.add_task(
        run_url_validation_task,
        validation_id=validation.id,
        urls=urls,
        proposed_schema=proposed_schema,
        name_validation=request_body.name_validation,
        description_validation=request_body.description_validation or "",
        ai_instruction=request_body.ai_instruction or "",
        token=auth_token,
    )

    return audit_schemas.AuditUrlValidationTaskResponse(
        task_id=validation.id,
        status=validation.status,
        total_urls=len(urls),
        message=f"Validación iniciada para {len(urls)} URLs — {request_body.name_validation}",
    )


@router.get(
    "/audits/url-validations",
    response_model=audit_schemas.AuditUrlValidationListResponse,
)
async def list_url_validations(
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(
            None, ge=1, le=100, description="Elementos por página (None para todos)"
        ),
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """Listar validaciones de URLs del usuario con paginación."""
    from sqlalchemy import text as sa_text

    # Contar total
    count_stmt = select(func.count()).select_from(AuditUrlValidation).where(
        AuditUrlValidation.user_id == current_user.id
    )
    total = (await session.execute(count_stmt)).scalar()

    # SELECT explícito — excluye results_json, global_report_ai_text y urls_raw (campos muy pesados)
    offset = (page - 1) * page_size if page_size is not None else 0
    limit_clause = f"LIMIT {page_size}" if page_size is not None else ""

    raw_sql = sa_text(f"""
        SELECT
            id,
            source_type,
            source_id,
            name_validation,
            description_validation,
            status,
            global_severity,
            input_tokens,
            output_tokens,
            error_message,
            report_pdf_path,
            report_word_path,
            global_report_pdf_path,
            global_report_word_path,
            created_at,
            completed_at
        FROM audit_url_validations
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        {limit_clause}
        OFFSET :offset
    """)

    result = await session.execute(raw_sql, {"user_id": str(current_user.id), "offset": offset})
    rows = result.mappings().all()

    return audit_schemas.AuditUrlValidationListResponse(
        items=[
            audit_schemas.AuditUrlValidationListItem(
                id=row["id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                name_validation=row["name_validation"],
                description_validation=row["description_validation"],
                status=row["status"],
                global_severity=row["global_severity"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                error_message=row["error_message"],
                report_pdf_path=row["report_pdf_path"],
                report_word_path=row["report_word_path"],
                global_report_pdf_path=row["global_report_pdf_path"],
                global_report_word_path=row["global_report_word_path"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/audits/url-validations/{validation_id}",
    response_model=audit_schemas.AuditUrlValidationDetailResponse,
)
async def get_url_validation(
        validation_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """Obtener detalle completo de una validación de URLs (incluye results_json)."""
    stmt = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación de URLs no encontrada",
        )

    return audit_schemas.AuditUrlValidationDetailResponse.model_validate(validation)


@router.post(
    "/audits/url-validations/{validation_id}/rerun",
    response_model=audit_schemas.AuditUrlValidationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Auditorías"],
)
async def rerun_url_validation(
        validation_id: UUID,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """
    Vuelve a ejecutar una validación de URLs completa sobre el mismo registro.
    Re-analiza todas las URLs conservando el mismo ID. No crea un registro nuevo.
    """
    stmt = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validación no encontrada")

    if validation.status == UrlValidationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La validación ya está en progreso",
        )

    # Re-resolver proposed_schema desde el source original
    schema_audit_service = get_schema_audit_service()
    proposed_schema = None

    if validation.source_type == UrlValidationSourceType.AUDIT_PAGE:
        source_obj = (await session.execute(
            select(AuditReport).where(AuditReport.id == validation.source_id)
        )).scalars().first()
        if source_obj:
            ai_suggestions = source_obj.ai_suggestions or {}
            proposal_text = ai_suggestions.get("content") or ai_suggestions.get("analysis")
            proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)
            if proposed_schema is None:
                proposed_schema = (source_obj.seo_analysis or {}).get("schema_markup", [])

    elif validation.source_type == UrlValidationSourceType.AUDIT_COMPARISON:
        source_obj = (await session.execute(
            select(AuditComparison).where(AuditComparison.id == validation.source_id)
        )).scalars().first()
        if source_obj:
            comparison_result = source_obj.comparison_result or {}
            proposal_text = comparison_result.get("ai_schema_comparison")
            proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)
            if proposed_schema is None:
                proposed_schema = comparison_result.get("raw_schemas", {}).get("base", [])

    if not proposed_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el esquema propuesto desde el source original",
        )

    # Re-parsear URLs desde urls_raw
    url_service = get_url_validation_service()
    urls = url_service.parse_urls(validation.urls_raw or "")

    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay URLs válidas para re-analizar",
        )

    # Resetear el registro para nueva ejecución
    validation.status = UrlValidationStatus.PENDING
    validation.results_json = []
    validation.global_severity = None
    validation.error_message = None
    validation.completed_at = None
    session.add(validation)
    await session.commit()

    auth_token = getattr(current_user, "_token", None) or "dummy-token"
    background_tasks.add_task(
        run_url_validation_task,
        validation_id=validation.id,
        urls=urls,
        proposed_schema=proposed_schema,
        name_validation=validation.name_validation,
        description_validation=validation.description_validation or "",
        ai_instruction=validation.ai_instruction or "",
        token=auth_token,
    )

    return audit_schemas.AuditUrlValidationTaskResponse(
        task_id=validation.id,
        status=UrlValidationStatus.PENDING,
        total_urls=len(urls),
        message=f"Re-ejecución iniciada para {len(urls)} URLs — {validation.name_validation}",
    )


@router.post(
    "/audits/url-validations/{validation_id}/rerun/{url:path}",
    response_model=audit_schemas.AuditUrlValidationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Auditorías"],
)
async def rerun_url_validation_single(
        validation_id: UUID,
        url: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """
    Vuelve a analizar una única URL dentro de una validación existente.
    Solo actualiza la entrada de esa URL en results_json. El resto se conserva intacto.
    """
    stmt = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validación no encontrada")

    if validation.status == UrlValidationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La validación ya está en progreso",
        )

    # Re-resolver proposed_schema desde el source original
    schema_audit_service = get_schema_audit_service()
    proposed_schema = None

    if validation.source_type == UrlValidationSourceType.AUDIT_PAGE:
        source_obj = (await session.execute(
            select(AuditReport).where(AuditReport.id == validation.source_id)
        )).scalars().first()
        if source_obj:
            ai_suggestions = source_obj.ai_suggestions or {}
            proposal_text = ai_suggestions.get("content") or ai_suggestions.get("analysis")
            proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)
            if proposed_schema is None:
                proposed_schema = (source_obj.seo_analysis or {}).get("schema_markup", [])

    elif validation.source_type == UrlValidationSourceType.AUDIT_COMPARISON:
        source_obj = (await session.execute(
            select(AuditComparison).where(AuditComparison.id == validation.source_id)
        )).scalars().first()
        if source_obj:
            comparison_result = source_obj.comparison_result or {}
            proposal_text = comparison_result.get("ai_schema_comparison")
            proposed_schema = schema_audit_service.extract_proposed_schema_from_text(proposal_text)
            if proposed_schema is None:
                proposed_schema = comparison_result.get("raw_schemas", {}).get("base", [])

    if not proposed_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el esquema propuesto desde el source original",
        )

    auth_token = getattr(current_user, "_token", None) or "dummy-token"
    background_tasks.add_task(
        run_url_validation_single_url_task,
        validation_id=validation.id,
        target_url=url,
        proposed_schema=proposed_schema,
        name_validation=validation.name_validation,
        description_validation=validation.description_validation or "",
        ai_instruction=validation.ai_instruction or "",
        token=auth_token,
    )

    return audit_schemas.AuditUrlValidationTaskResponse(
        task_id=validation.id,
        status=UrlValidationStatus.IN_PROGRESS,
        total_urls=1,
        message=f"Re-análisis iniciado para: {url}",
    )


@router.get(
    "/audits/url-validations/{validation_id}/schemas",
    response_model=audit_schemas.AuditUrlValidationSchemasResponse,
)
async def list_url_validation_schemas(
        validation_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """Devuelve todos los esquemas escaneados de una validación de URLs en un arreglo por ID."""
    stmt = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación de URLs no encontrada",
        )

    raw_results = validation.results_json or []
    schemas = [
        audit_schemas.AuditUrlValidationSchemaItem(
            url=item.get("url", ""),
            schema_types_found=item.get("schema_types_found"),
            extracted_schemas=item.get("extracted_schemas"),
            validation_errors=item.get("validation_errors"),
            severity=item.get("severity"),
            ai_report=item.get("ai_report"),
            error=item.get("error"),
            comparison_table=item.get("comparison_table"),
        )
        for item in raw_results
        if isinstance(item, dict)
    ]

    return audit_schemas.AuditUrlValidationSchemasResponse(
        validation_id=validation.id,
        name_validation=validation.name_validation,
        status=validation.status,
        global_severity=validation.global_severity,
        total=len(schemas),
        schemas=schemas,
    )


@router.get(
    "/audits/url-validations/{validation_id}/schemas/public",
    response_model=audit_schemas.AuditUrlValidationSchemasResponse,
    tags=["Público"],
)
async def list_url_validation_schemas_public(
        validation_id: UUID,
        session=Depends(get_session),
):
    """Endpoint público: devuelve los esquemas de una validación de URLs sin requerir autenticación."""
    stmt = select(AuditUrlValidation).where(
        AuditUrlValidation.id == validation_id,
    )
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación de URLs no encontrada",
        )

    raw_results = validation.results_json or []
    schemas = [
        audit_schemas.AuditUrlValidationSchemaItem(
            url=item.get("url", ""),
            schema_types_found=item.get("schema_types_found"),
            extracted_schemas=item.get("extracted_schemas"),
            validation_errors=item.get("validation_errors"),
            severity=item.get("severity"),
            ai_report=item.get("ai_report"),
            error=item.get("error"),
            comparison_table=item.get("comparison_table"),
        )
        for item in raw_results
        if isinstance(item, dict)
    ]

    return audit_schemas.AuditUrlValidationSchemasResponse(
        validation_id=validation.id,
        name_validation=validation.name_validation,
        status=validation.status,
        global_severity=validation.global_severity,
        total=len(schemas),
        schemas=schemas,
    )


# ---------------------------------------------------------------------------
# Comentarios públicos de validaciones de URL
# ---------------------------------------------------------------------------

@router.get(
    "/audits/url-validations/{validation_id}/schemas/public/comments",
    response_model=audit_schemas.CommentListResponse,
    tags=["Público"],
)
async def list_url_validation_comments(
        validation_id: UUID,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        session=Depends(get_session),
):
    """
    Endpoint público: lista paginada de comentarios de una validación de URLs.
    No requiere autenticación.
    """
    stmt_total = select(func.count()).select_from(UrlValidationComment).where(
        UrlValidationComment.validation_id == validation_id
    )
    total = (await session.execute(stmt_total)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(UrlValidationComment)
        .where(UrlValidationComment.validation_id == validation_id)
        .order_by(UrlValidationComment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()

    return audit_schemas.CommentListResponse(
        validation_id=validation_id,
        total=total,
        page=page,
        page_size=page_size,
        items=[audit_schemas.CommentResponse.model_validate(c) for c in items],
    )


@router.post(
    "/audits/url-validations/schema/public/{url:path}/comment",
    response_model=audit_schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Público"],
)
async def create_url_validation_comment(
        url: str,
        validation_id: UUID = Query(..., description="ID de la AuditUrlValidation a la que pertenece la URL"),
        body: audit_schemas.CommentCreate = ...,
        session=Depends(get_session),
):
    """
    Endpoint público: crea un comentario sobre un schema item identificado por su URL.
    Requiere validation_id como query param para evitar escaneos costosos.
    No requiere autenticación.
    """
    stmt = select(AuditUrlValidation).where(AuditUrlValidation.id == validation_id)
    validation = (await session.execute(stmt)).scalars().first()

    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación no encontrada",
        )

    comment = UrlValidationComment(
        validation_id=validation.id,
        schema_item_url=url,
        username=body.username,
        comment=body.comment,
        status=CommentStatus.PENDING,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return audit_schemas.CommentResponse.model_validate(comment)


@router.patch(
    "/audits/url-validations/schema/comments/{comment_id}/answer",
    response_model=audit_schemas.CommentResponse,
    tags=["Auditorías"],
)
async def answer_url_validation_comment(
        comment_id: UUID,
        body: audit_schemas.CommentAnswerUpdate,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """
    Responde a un comentario y cambia su estado (done | rejected).
    Solo el dueño de la validación puede usar este endpoint.
    """
    stmt = select(UrlValidationComment).where(UrlValidationComment.id == comment_id)
    comment = (await session.execute(stmt)).scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado")

    # Verificar que el usuario autenticado es dueño de la validación
    stmt_v = select(AuditUrlValidation).where(
        AuditUrlValidation.id == comment.validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt_v)).scalars().first()
    if not validation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para responder este comentario",
        )

    allowed_statuses = {s.value for s in CommentStatus}
    if body.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Estado inválido. Valores permitidos: {allowed_statuses}",
        )

    comment.answer = body.answer
    comment.status = CommentStatus(body.status)
    comment.answered_at = datetime.utcnow()

    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return audit_schemas.CommentResponse.model_validate(comment)


@router.delete(
    "/audits/url-validations/schema/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auditorías"],
)
async def delete_url_validation_comment(
        comment_id: UUID,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """
    Elimina un comentario.
    Solo el dueño de la validación puede eliminar comentarios.
    """
    stmt = select(UrlValidationComment).where(UrlValidationComment.id == comment_id)
    comment = (await session.execute(stmt)).scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado")

    stmt_v = select(AuditUrlValidation).where(
        AuditUrlValidation.id == comment.validation_id,
        AuditUrlValidation.user_id == current_user.id,
    )
    validation = (await session.execute(stmt_v)).scalars().first()
    if not validation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este comentario",
        )

    await session.delete(comment)
    await session.commit()


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
    Devuelve la misma estructura que antes pero con SELECT optimizado (sin JSONB pesados).
    """
    # Filtros base
    filters = [AuditReport.user_id == current_user.id]
    if web_page_id:
        filters.append(AuditReport.web_page_id == web_page_id)
    if status_filter:
        filters.append(sql_cast(AuditReport.status, String) == status_filter.value)

    # Contar total con COUNT() en la BD (evita cargar todo en memoria)
    count_statement = select(func.count()).select_from(AuditReport).where(*filters)
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Solo las columnas necesarias para la tabla + columnas ligeras de web_page via JOIN
    # Se excluyen: lighthouse_data, ai_suggestions, seo_analysis (JSONB muy pesados)
    statement = select(
        AuditReport.id,
        AuditReport.web_page_id,
        AuditReport.user_id,
        AuditReport.status,
        AuditReport.performance_score,
        AuditReport.seo_score,
        AuditReport.accessibility_score,
        AuditReport.best_practices_score,
        AuditReport.lcp,
        AuditReport.fid,
        AuditReport.cls,
        AuditReport.report_pdf_path,
        AuditReport.report_excel_path,
        AuditReport.report_word_path,
        AuditReport.error_message,
        AuditReport.created_at,
        AuditReport.completed_at,
        # Columnas ligeras de web_page (sin manual_html_content)
        WebPage.id.label("wp_id"),
        WebPage.url.label("wp_url"),
        WebPage.name.label("wp_name"),
        WebPage.instructions.label("wp_instructions"),
        WebPage.tech_stack.label("wp_tech_stack"),
        WebPage.tags.label("wp_tags"),
        WebPage.provider.label("wp_provider"),
        WebPage.is_active.label("wp_is_active"),
    ).join(WebPage, AuditReport.web_page_id == WebPage.id, isouter=True).where(
        *filters
    ).order_by(desc(AuditReport.created_at))

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    rows = result.all()

    # Verificar y generar reportes faltantes para auditorías completadas
    audits_to_update = []
    items = []
    for row in rows:
        pdf_path = row.report_pdf_path
        excel_path = row.report_excel_path
        word_path = row.report_word_path

        if row.status == AuditStatus.COMPLETED and (not pdf_path or not excel_path or not word_path):
            try:
                audit_obj = await session.get(AuditReport, row.id)
                if audit_obj:
                    report_paths = ReportGenerator(audit=audit_obj).generate_all()
                    audit_obj.report_pdf_path = report_paths.get('pdf_path')
                    audit_obj.report_excel_path = report_paths.get('xlsx_path')
                    audit_obj.report_word_path = report_paths.get('word_path')
                    session.add(audit_obj)
                    audits_to_update.append(audit_obj)
                    pdf_path = audit_obj.report_pdf_path
                    excel_path = audit_obj.report_excel_path
                    word_path = audit_obj.report_word_path
            except Exception as e:
                print(f"⚠️ Error generando reportes en listado para audit {row.id}: {e}")

        # Construir web_page anidado con la misma estructura que espera el frontend
        web_page_data = None
        if row.wp_id:
            web_page_data = audit_schemas.WebPageSimpleResponse(
                id=row.wp_id,
                url=row.wp_url,
                name=row.wp_name,
                instructions=row.wp_instructions,
                tech_stack=row.wp_tech_stack,
                tags=row.wp_tags,
                provider=row.wp_provider,
                is_active=row.wp_is_active,
            )

        items.append(audit_schemas.AuditListItem(
            id=row.id,
            web_page_id=row.web_page_id,
            user_id=row.user_id,
            status=row.status,
            performance_score=row.performance_score,
            seo_score=row.seo_score,
            accessibility_score=row.accessibility_score,
            best_practices_score=row.best_practices_score,
            lcp=row.lcp,
            fid=row.fid,
            cls=row.cls,
            lighthouse_data=None,
            ai_suggestions=None,
            report_pdf_path=pdf_path,
            report_excel_path=excel_path,
            report_word_path=word_path,
            error_message=row.error_message,
            created_at=row.created_at,
            completed_at=row.completed_at,
            web_page=web_page_data,
        ))

    if audits_to_update:
        await session.commit()

    return audit_schemas.AuditListResponse(
        items=items,
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

