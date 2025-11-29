"""
Dependencias de seguridad y middleware.
Implementa la lógica de "Shadow User" - sincronización automática con API externa.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_session
from app.models.user import User
from app.services.auth_provider import auth_provider
from app.schemas.auth_schemas import VerifyTokenResponse


# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Middleware de Seguridad Principal - Shadow User Logic

    Flujo:
    1. Extraer el token Bearer del header
    2. Verificar el token en la API Externa
    3. Si es válido, buscar el usuario en la BD Local
    4. Si no existe localmente -> INSERT (crear shadow user)
    5. Si existe -> UPDATE (sincronizar datos)
    6. Retornar el objeto User local

    Args:
        credentials: Token Bearer del header Authorization
        session: Sesión de base de datos

    Returns:
        User: Objeto de usuario sincronizado

    Raises:
        HTTPException 401: Si el token es inválido o expirado
        HTTPException 503: Si la API externa no está disponible
    """
    token = credentials.credentials

    # 1. Verificar token en API Externa
    try:
        external_user: VerifyTokenResponse = await auth_provider.verify_token(token)
    except HTTPException as e:
        # Re-lanzar excepciones de autenticación
        raise e

    # 2. Buscar usuario en BD Local por external_id
    external_id = UUID(external_user.user_id)

    statement = select(User).where(User.external_id == external_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    # 3. Si no existe -> Crear Shadow User
    if user is None:
        user = User(
            external_id=external_id,
            email=external_user.user_email,
            full_name=external_user.user_name,
            tenant_id=UUID(external_user.tenant_id) if external_user.tenant_id else None,
            project_id=UUID(external_user.project_id) if external_user.project_id else None,
            last_synced_at=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # 4. Si existe -> Sincronizar datos actualizados
    else:
        user.email = external_user.user_email
        user.full_name = external_user.user_name
        user.tenant_id = UUID(external_user.tenant_id) if external_user.tenant_id else None
        user.project_id = UUID(external_user.project_id) if external_user.project_id else None
        user.last_synced_at = datetime.utcnow()

        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    Versión opcional del middleware - permite acceso sin autenticación.
    Útil para endpoints públicos que pueden tener funcionalidad adicional si hay usuario.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None

