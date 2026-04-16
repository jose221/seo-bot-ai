"""
Endpoints para gestión de Targets (WebPages).
CRUD completo para sitios web a auditar.
"""
from typing import Optional, List
from sqlalchemy import or_, func, any_

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import joinedload
from sqlmodel import select, desc
from uuid import UUID
from datetime import datetime

from app.core.database import get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.webpage import WebPage
from app.schemas import target_schemas

router = APIRouter()


@router.post("/targets", response_model=target_schemas.WebPageResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
        target: target_schemas.WebPageCreate,
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Crear un nuevo target para auditar.
    Requiere autenticación.
    """
    # Verificar si la URL ya existe para este usuario
    statement = select(WebPage).where(
        WebPage.user_id == current_user.id,
        WebPage.url == target.url,
        WebPage.is_active == True
    )
    result = await session.execute(statement)
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un target activo con la URL: {target.url}"
        )

    # Crear nuevo target
    db_target = WebPage(
        user_id=current_user.id,
        url=target.url,
        name=target.name or target.url,
        instructions=target.instructions,
        tech_stack=target.tech_stack,
        manual_html_content=target.manual_html_content,
        tags=target.tags or [],
        provider=target.provider
    )

    session.add(db_target)
    await session.commit()
    await session.refresh(db_target)

    return db_target


@router.get("/targets", response_model=target_schemas.WebPageListResponse)
async def list_targets(
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
        is_active: bool = Query(True, description="Filtrar por activos/inactivos"),
        tag: Optional[str] = Query(None, description="Filtrar por un tag específico"),
        provider: Optional[str] = Query(None, description="Filtrar por proveedor"),
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Listar targets del usuario autenticado.
    Soporta paginación y filtros por tag y provider.
    """
    # Filtros base
    filters = [
        WebPage.user_id == current_user.id,
        WebPage.is_active == is_active
    ]
    if tag:
        filters.append(tag == any_(WebPage.tags))
    if provider:
        filters.append(WebPage.provider == provider)

    # Solo seleccionar columnas necesarias para el listado (evita manual_html_content y audit_reports pesados)
    statement = select(
        WebPage.id,
        WebPage.user_id,
        WebPage.url,
        WebPage.name,
        WebPage.instructions,
        WebPage.tech_stack,
        WebPage.tags,
        WebPage.provider,
        WebPage.is_active,
        WebPage.created_at,
        WebPage.updated_at,
    ).where(*filters).order_by(desc(WebPage.created_at))

    # Contar total usando COUNT() en la BD (evita cargar todo en memoria)
    count_statement = select(func.count()).select_from(WebPage).where(*filters)
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Paginación
    if page_size is not None:
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

    result = await session.execute(statement)
    targets = result.all()

    return target_schemas.WebPageListResponse(
        items=[
            target_schemas.WebPageListItem(
                id=t.id, user_id=t.user_id, url=t.url, name=t.name,
                instructions=t.instructions, tech_stack=t.tech_stack,
                tags=t.tags, provider=t.provider, is_active=t.is_active,
                created_at=t.created_at, updated_at=t.updated_at,
            )
            for t in targets
        ],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/targets/search", response_model=target_schemas.WebPageSearchResponse)
async def search_targets(
  query: Optional[str] = Query(None, description="Query de búsqueda por nombre o url"),
  is_active: bool = Query(True, description="Filtrar por activos/inactivos"),
  only_page_with_audits_completed: bool = Query(False, description="Mostrar solo páginas con auditorías completadas"),
  exclude_web_page_id: Optional[UUID] = Query(None, description="ID de web_page a excluir de los resultados"),
  tag: Optional[str] = Query(None, description="Filtrar por un tag específico"),
  provider: Optional[str] = Query(None, description="Filtrar por proveedor"),
  page: int = Query(1, ge=1, description="Número de página"),
  page_size: Optional[int] = Query(None, ge=1, le=100, description="Elementos por página (None para todos)"),
  current_user: User = Depends(get_current_user),
  session = Depends(get_session)
):
  """
  Buscar targets del usuario autenticado por nombre o url.
  Soporta paginación y filtros por tag y provider.
  """
  filters = [
    WebPage.user_id == current_user.id,
    WebPage.is_active == is_active
  ]
  if query:
    filters.append(
      or_(
        WebPage.name.ilike(f"%{query}%"),
        WebPage.url.ilike(f"%{query}%")
      )
    )

  # Excluir un web_page_id específico si se proporciona
  if exclude_web_page_id is not None:
    filters.append(WebPage.id != exclude_web_page_id)

  if tag:
    filters.append(tag == any_(WebPage.tags))
  if provider:
    filters.append(WebPage.provider == provider)

  # Solo seleccionar las columnas necesarias
  statement = select(
    WebPage.id,
    WebPage.url,
    WebPage.name,
    WebPage.tags,
    WebPage.provider,
    WebPage.is_active,
    WebPage.created_at
  ).where(*filters)

  # Si se requiere filtrar por páginas con auditorías completadas
  if only_page_with_audits_completed:
    from app.models.audit import AuditReport, AuditStatus
    statement = statement.join(AuditReport, WebPage.id == AuditReport.web_page_id).where(
      AuditReport.status == AuditStatus.COMPLETED.value
    ).distinct()

  statement = statement.order_by(desc(WebPage.created_at))

  count_statement = select(func.count()).select_from(WebPage).where(*filters)
  if only_page_with_audits_completed:
    from app.models.audit import AuditReport, AuditStatus
    count_statement = select(func.count(WebPage.id.distinct())).select_from(WebPage).join(
      AuditReport, WebPage.id == AuditReport.web_page_id
    ).where(*filters).where(AuditReport.status == AuditStatus.COMPLETED.value)

  count_result = await session.execute(count_statement)
  total = count_result.scalar()

  if page_size is not None:
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)

  result = await session.execute(statement)
  targets = result.all()

  return target_schemas.WebPageSearchResponse(
    items=[
      target_schemas.WebPageSearchItem(
        id=t.id, url=t.url, name=t.name,
        tags=t.tags, provider=t.provider, is_active=t.is_active
      )
      for t in targets
    ],
    total=total,
    page=page,
    page_size=page_size
  )


@router.get("/targets/tags", response_model=target_schemas.TagsListResponse)
async def list_tags(
  current_user: User = Depends(get_current_user),
  session = Depends(get_session)
):
  """
  Obtener todos los tags distintos del usuario autenticado.
  Útil para construir filtros en el front-end.
  """
  from sqlalchemy import text
  # Usamos unnest para aplanar el array de tags y obtener distintos
  stmt = text(
    "SELECT DISTINCT unnest(tags) AS tag FROM web_pages "
    "WHERE user_id = :user_id AND is_active = true AND tags IS NOT NULL "
    "ORDER BY tag"
  )
  result = await session.execute(stmt, {"user_id": str(current_user.id)})
  tags = [row[0] for row in result.all()]

  return target_schemas.TagsListResponse(tags=tags, total=len(tags))


@router.get("/targets/{target_id}", response_model=target_schemas.WebPageResponse)
async def get_target(
        target_id: UUID,
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Obtener un target específico por ID.
    Solo el propietario puede acceder.
    """
    statement = select(WebPage).where(
        WebPage.id == target_id,
        WebPage.user_id == current_user.id
    ).options(joinedload(WebPage.audit_reports))
    result = await session.execute(statement)
    target = result.unique().scalars().first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target no encontrado"
        )

    return target


@router.patch("/targets/{target_id}", response_model=target_schemas.WebPageResponse)
async def update_target(
        target_id: UUID,
        target_update: target_schemas.WebPageUpdate,
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Actualizar un target existente.
    Solo el propietario puede modificar.
    """
    statement = select(WebPage).where(
        WebPage.id == target_id,
        WebPage.user_id == current_user.id
    )
    result = await session.execute(statement)
    target = result.scalars().first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target no encontrado"
        )

    # Actualizar solo campos proporcionados
    update_data = target_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(target, key, value)

    target.updated_at = datetime.utcnow()

    session.add(target)
    await session.commit()
    await session.refresh(target)

    return target


@router.patch("/targets/{target_id}/html", response_model=target_schemas.WebPageResponse)
async def update_target_html(
        target_id: UUID,
        body: target_schemas.WebPageHtmlUpdate,
        current_user: User = Depends(get_current_user),
        session=Depends(get_session),
):
    """
    Actualiza el contenido HTML manual guardado para un target.
    Útil para proporcionar HTML cuando el sitio bloquea el scraping automático.
    Requiere autenticación.
    """
    statement = select(WebPage).where(
        WebPage.id == target_id,
        WebPage.user_id == current_user.id,
    )
    target = (await session.execute(statement)).scalars().first()

    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target no encontrado")

    target.manual_html_content = body.manual_html_content
    target.updated_at = datetime.utcnow()
    session.add(target)
    await session.commit()
    await session.refresh(target)

    return target


@router.get(
    "/targets/html/{target_url:path}",
    response_model=target_schemas.HtmlContentResponse,
    tags=["Público"],
)
async def get_target_html(
        target_url: str,
        session=Depends(get_session),
):
    """
    Obtiene el HTML completo de un target buscado por su URL.
    Intenta hacer scraping en tiempo real (Playwright + Nodriver como fallback antibot).
    Si el sitio bloquea el acceso, devuelve el HTML guardado en el target.
    Endpoint público, no requiere autenticación.

    Ejemplo: GET /targets/html/https://example.com
    """
    from urllib.parse import unquote
    from uuid import uuid4
    target_url = unquote(target_url)
    statement = select(WebPage).where(WebPage.url == target_url, WebPage.is_active == True)
    target = (await session.execute(statement)).scalars().first()

    # Intentar scraping en tiempo real (tanto si existe en tabla como si no)
    html: Optional[str] = None
    source = "live"

    try:
        from app.services.audit_engine import get_audit_engine
        engine = get_audit_engine()
        html = await engine.fetch_html(target.url if target else target_url, timeout_ms=30_000)
    except Exception as scrape_err:
        print(f"⚠️  Scraping bloqueado para {target_url}: {scrape_err} — intentando fallback")
        html = None

    # Fallback al HTML guardado si el scraping falló y existe en tabla
    if not html and target and target.manual_html_content:
        html = target.manual_html_content
        source = "stored"

    # Si no se pudo obtener HTML de ninguna forma
    if not html:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo acceder a su HTML. No fue posible obtener el contenido mediante scraping"
                   + (" ni hay contenido guardado para este target." if target else
                      " y la URL no está registrada como target."),
        )

    return target_schemas.HtmlContentResponse(
        target_id=target.id if target else uuid4(),
        url=target.url if target else target_url,
        html=html,
        source=source,
        html_length=len(html),
    )


@router.delete("/targets/{target_id}", response_model=target_schemas.DeleteTargetResponse)
async def delete_target(
        target_id: UUID,
        hard_delete: bool = Query(False, description="Si es True, borra físicamente"),
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Eliminar un target.
    Por defecto es soft delete (marca como inactivo).
    """
    statement = select(WebPage).where(
        WebPage.id == target_id,
        WebPage.user_id == current_user.id
    )
    result = await session.execute(statement)
    target = result.scalars().first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target no encontrado"
        )

    try:
        if hard_delete:
            await session.delete(target)
            message = "Target eliminado permanentemente"
            print(f"🗑️  Target {target_id} eliminado permanentemente (hard delete)")
        else:
            target.is_active = False
            target.updated_at = datetime.utcnow()
            session.add(target)
            message = "Target desactivado (soft delete)"
            print(f"🔒 Target {target_id} desactivado (soft delete)")

        await session.commit()

        return {
            "success": True,
            "message": message,
            "target_id": str(target_id),
            "hard_delete": hard_delete
        }
    except Exception as e:
        await session.rollback()
        print(f"❌ Error en DELETE target {target_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al eliminar target: {str(e)}"
        )

