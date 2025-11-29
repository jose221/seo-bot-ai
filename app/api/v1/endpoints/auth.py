"""
Endpoints de Autenticación - Proxy a la API externa de Herandro Services.
Actúa como pasarela para login y registro.
"""
from fastapi import APIRouter, status

from app.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse
)
from app.services.auth_provider import auth_provider


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    **Endpoint de Login** - Proxy a la API externa

    Recibe credenciales del usuario y las reenvía a la API de Herandro.
    Si las credenciales son válidas, retorna el token de acceso.

    **Flujo:**
    1. Usuario envía email + password al Bot
    2. Bot reenvía a Herandro Services API
    3. Si válido -> Retorna access_token
    4. Si inválido -> Retorna 401

    **Nota:** El token retornado debe incluirse en todas las peticiones subsecuentes
    en el header `Authorization: Bearer {token}`
    """
    return await auth_provider.login(credentials)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest):
    """
    **Endpoint de Registro** - Proxy a la API externa

    Registra un nuevo usuario en el sistema de Herandro Services.
    Retorna automáticamente un token de acceso tras el registro exitoso.

    **Flujo:**
    1. Usuario envía datos de registro al Bot
    2. Bot reenvía a Herandro Services API
    3. Si exitoso -> Retorna access_token + datos de usuario
    4. Si el email ya existe -> Retorna 400

    **Campos requeridos:**
    - email: Correo electrónico único
    - password: Contraseña (mínimo 8 caracteres)
    - full_name: Nombre completo
    - username: Nombre de usuario único
    - city: Ciudad
    - country_code: Código ISO del país (ej: "MX")
    """
    return await auth_provider.register(user_data)


@router.get("/me")
async def get_current_user_info():
    """
    **Información del usuario actual** - Endpoint protegido de ejemplo

    Este endpoint requiere autenticación.
    Retorna información básica del usuario autenticado.

    **Uso:** Útil para verificar que el token funciona correctamente.
    """
    return {
        "message": "This endpoint requires authentication",
        "detail": "Use the get_current_user dependency in protected endpoints"
    }

