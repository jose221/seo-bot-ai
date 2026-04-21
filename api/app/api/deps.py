"""
Dependencias de seguridad — Keycloak JWT + sincronización automática de usuario.

Flujo (Shadow User con Keycloak):
  1. Extraer y validar el Bearer JWT contra las llaves públicas de Keycloak (JWKS).
  2. Extraer el email del payload JWT.
  3. Buscar el usuario en la BD local por email.
  4. Si no existe → INSERT (crear shadow user con datos del token).
  5. Si existe → retornar el usuario local actualizado.
"""
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import (
    _decode_token,
    _get_jwks,
    oauth2_scheme,
    set_request_auth_context,
)
from app.models.user import User

log = logging.getLogger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Dependencia principal de seguridad — Keycloak JWT + Shadow User.

    1. Valida el JWT contra las llaves públicas de Keycloak.
    2. Busca al usuario por email en la BD local.
    3. Si no existe, lo crea automáticamente con los datos del token.
    4. Almacena el token en el contexto del request (disponible vía get_request_access_token).
    """
    token = credentials.credentials

    # 1. Validar JWT con Keycloak JWKS
    try:
        jwks = await _get_jwks()
        payload: dict[str, Any] = _decode_token(token, jwks)
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Error inesperado al validar token Keycloak: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # 2. Extraer datos del usuario del JWT
    keycloak_sub: str | None = payload.get("sub")
    email: str | None = payload.get("email")
    preferred_username: str | None = payload.get("preferred_username")
    full_name: str = payload.get("name") or (
        f"{payload.get('given_name', '')} {payload.get('family_name', '')}".strip()
    ) or preferred_username or "Unknown"

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain an email claim",
        )

    # 3. Buscar usuario por email en la BD local
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    user: User | None = result.scalar_one_or_none()

    # 4. Si no existe → crearlo (Shadow User)
    if user is None:
        log.info("Creando shadow user para email=%s sub=%s", email, keycloak_sub)
        try:
            keycloak_uuid = UUID(keycloak_sub) if keycloak_sub else None
        except (ValueError, AttributeError):
            keycloak_uuid = None

        user = User(
            external_id=keycloak_uuid,
            email=email,
            full_name=full_name,
            username=preferred_username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        log.info("Shadow user creado — id=%s email=%s", user.id, user.email)
    else:
        log.debug("Usuario encontrado en BD — id=%s email=%s", user.id, user.email)

    # 5. Guardar token en el contexto del request
    set_request_auth_context(token=token, payload=payload)
    setattr(user, "_token", token)

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Versión opcional — permite acceso sin autenticación.
    Útil para endpoints públicos con funcionalidad extra si hay usuario.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None


