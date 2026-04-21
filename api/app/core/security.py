"""Módulo de seguridad — Keycloak UMA (Resource + Scope).

Validación de permisos directamente contra el endpoint de token de
Keycloak usando grant_type=urn:ietf:params:oauth:grant-type:uma-ticket.

Modelo de permisos:
    resource_guard("audits") → _scopes("canRead")
    → Keycloak valida: resource=audits, scope=canRead
"""

import logging
from contextvars import ContextVar
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTPBearer scheme — Swagger UI mostrará un campo simple para pegar el token
# ---------------------------------------------------------------------------

oauth2_scheme = HTTPBearer(auto_error=True)

_KEYCLOAK_TOKEN_URL = (
    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/realms/"
    f"{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
)

_KEYCLOAK_JWKS_URL = (
    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/realms/"
    f"{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
)

_KEYCLOAK_ISSUER = (
    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
)

_jwks_cache: dict[str, Any] | None = None
_request_access_token_ctx: ContextVar[str | None] = ContextVar(
    "request_access_token_ctx",
    default=None,
)
_request_user_payload_ctx: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_user_payload_ctx",
    default=None,
)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

async def _get_jwks() -> dict[str, Any]:
    """Obtiene las llaves públicas de Keycloak (con cache)."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    log.debug("Obteniendo JWKS de %s", _KEYCLOAK_JWKS_URL)
    async with httpx.AsyncClient() as client:
        response = await client.get(_KEYCLOAK_JWKS_URL)
        response.raise_for_status()
        _jwks_cache = response.json()
        log.debug("JWKS obtenido correctamente (%d keys)", len(_jwks_cache.get("keys", [])))
        return _jwks_cache


def _decode_token(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    """Decodifica y valida el JWT usando las llaves públicas de Keycloak."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            log.warning("No se encontró llave con kid=%s en JWKS", kid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=_KEYCLOAK_ISSUER,
            options={
                "verify_aud": False,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
        return payload

    except JWTError as e:
        log.warning("Error al decodificar JWT: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def _check_uma_permission(token: str, resource: str, scope: str) -> bool:
    """Consulta a Keycloak si el token tiene acceso al resource#scope vía UMA."""
    permission_str = f"{resource}#{scope}"

    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
        "audience": settings.KEYCLOAK_CLIENT_ID,
        "permission": permission_str,
        "response_mode": "decision",
    }

    headers = {"Authorization": f"Bearer {token}"}

    log.debug(
        "UMA check → url=%s resource=%s scope=%s",
        _KEYCLOAK_TOKEN_URL, resource, scope,
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(_KEYCLOAK_TOKEN_URL, data=data, headers=headers)

    log.debug("UMA response → status=%d body=%s", response.status_code, response.text[:500])
    return response.status_code == 200


# ---------------------------------------------------------------------------
# PermissionChecker — dependencia de FastAPI
# ---------------------------------------------------------------------------

class PermissionChecker:
    """Dependencia callable para validar resource + scope contra Keycloak UMA.

    Equivalente a ``@Resource("audits") + @Scopes("canRead")`` de NestJS.

    Uso::

        @router.get("/", dependencies=[Depends(PermissionChecker("audits", "canRead"))])
    """

    def __init__(self, resource: str, scope: str):
        self.resource = resource
        self.scope = scope

    async def __call__(
        self, credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
    ) -> dict[str, Any]:
        token = credentials.credentials
        jwks = await _get_jwks()
        payload = _decode_token(token, jwks)

        log.debug(
            "Token validado — sub=%s preferred_username=%s",
            payload.get("sub"),
            payload.get("preferred_username"),
        )

        has_permission = await _check_uma_permission(token, self.resource, self.scope)

        if not has_permission:
            log.warning(
                "Permission denied — user=%s resource=%s scope=%s",
                payload.get("preferred_username", payload.get("sub")),
                self.resource,
                self.scope,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for resource '{self.resource}' with scope '{self.scope}'",
            )

        log.debug(
            "Permission granted — user=%s resource=%s scope=%s",
            payload.get("preferred_username", payload.get("sub")),
            self.resource,
            self.scope,
        )

        set_request_auth_context(token=token, payload=payload)
        return payload


# ---------------------------------------------------------------------------
# resource_guard — Factory para el patrón @Resource + @Scopes
# ---------------------------------------------------------------------------

def resource_guard(resource: str):
    """Equivalente a ``@Resource('audits')`` de NestJS/nest-keycloak-connect.

    Devuelve un factory de scopes enlazado al recurso dado::

        # Al inicio del router — define el resource
        _scopes = resource_guard("audits")

        # En cada endpoint — define el scope
        @router.get("/", dependencies=[Depends(_scopes("canRead"))])
        @router.post("/", dependencies=[Depends(_scopes("canCreate"))])
    """

    def scopes(*scope_names: str) -> PermissionChecker:
        if len(scope_names) != 1:
            raise ValueError(
                f"resource_guard('{resource}') espera exactamente 1 scope, "
                f"recibió {len(scope_names)}: {scope_names}"
            )
        return PermissionChecker(resource=resource, scope=scope_names[0])

    return scopes


# ---------------------------------------------------------------------------
# Helpers de contexto de request
# ---------------------------------------------------------------------------

def set_request_auth_context(token: str, payload: dict[str, Any]) -> None:
    """Guarda token y payload del usuario durante el ciclo de vida del request."""
    _request_access_token_ctx.set(token)
    _request_user_payload_ctx.set(payload)


def clear_request_auth_context() -> None:
    """Limpia el contexto de autenticación asociado al request actual."""
    _request_access_token_ctx.set(None)
    _request_user_payload_ctx.set(None)


def get_request_access_token() -> str | None:
    """Retorna el token actual del request, o ``None`` si aún no se autenticó."""
    return _request_access_token_ctx.get()


def get_request_user_payload() -> dict[str, Any] | None:
    """Retorna el payload JWT del request, o ``None`` si aún no se autenticó."""
    return _request_user_payload_ctx.get()


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """Devuelve el payload del token JWT decodificado y guarda el contexto."""
    jwks = await _get_jwks()
    payload = _decode_token(credentials.credentials, jwks)
    set_request_auth_context(token=credentials.credentials, payload=payload)
    return payload


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> str | None:
    """Devuelve el ``sub`` (Keycloak user id) del token."""
    jwks = await _get_jwks()
    payload = _decode_token(credentials.credentials, jwks)
    set_request_auth_context(token=credentials.credentials, payload=payload)
    return payload.get("sub")
