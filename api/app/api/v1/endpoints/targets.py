"""
Endpoints para gestión de Targets (WebPages).
CRUD completo para sitios web a auditar.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import joinedload
from sqlmodel import select, desc
from uuid import UUID
from datetime import datetime, timezone

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
        tech_stack=target.tech_stack
    )

    session.add(db_target)
    await session.commit()
    await session.refresh(db_target)

    return db_target


@router.get("/targets", response_model=target_schemas.WebPageListResponse)
async def list_targets(
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: int = Query(10, ge=1, le=100, description="Elementos por página"),
        is_active: bool = Query(True, description="Filtrar por activos/inactivos"),
        current_user: User = Depends(get_current_user),
        session = Depends(get_session)
):
    """
    Listar targets del usuario autenticado.
    Soporta paginación.
    """
    # Query base
    statement = select(WebPage).where(
        WebPage.user_id == current_user.id,
        WebPage.is_active == is_active
    ).order_by(desc(WebPage.created_at))

    # Contar total
    count_statement = select(WebPage).where(
        WebPage.user_id == current_user.id,
        WebPage.is_active == is_active
    )
    count_result = await session.execute(count_statement)
    total = len(count_result.scalars().all())

    # Paginación
    offset = (page - 1) * page_size
    statement = statement.options(joinedload(WebPage.audit_reports)).offset(offset).limit(page_size)

    result = await session.execute(statement)
    targets = result.unique().scalars().all()

    return target_schemas.WebPageListResponse(
        items=targets,
        total=total,
        page=page,
        page_size=page_size
    )


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
    target = result.scalars().first()

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

    target.updated_at = datetime.now(timezone.utc)

    session.add(target)
    await session.commit()
    await session.refresh(target)

    return target


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
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

    if hard_delete:
        await session.delete(target)
    else:
        target.is_active = False
        target.updated_at = datetime.now(timezone.utc)
        session.add(target)

    await session.commit()
    return None

