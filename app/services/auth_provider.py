"""
Cliente HTTP para la API externa de Autenticación (Herandro Services).
Actúa como proxy para login, registro y verificación de tokens.
"""
import httpx

from app.core.config import settings
from app.core.http_handler import HTTPResponseHandler
from app.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyTokenResponse
)


class AuthProvider:
    """Cliente para interactuar con la API externa de autenticación"""

    def __init__(self):
        self.base_url = settings.HERANDRO_API_URL
        self.timeout = 30.0

    async def login(self, credentials: LoginRequest) -> LoginResponse:
        """
        Envía credenciales a la API externa y retorna el token.

        Args:
            credentials: Email y password del usuario

        Returns:
            LoginResponse con access_token y datos del usuario

        Raises:
            HTTPException: Si las credenciales son inválidas o hay error de conexión
        """
        url = f"{self.base_url}/auth/login"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=credentials.model_dump(mode='json', exclude_none=True)
                )

                return HTTPResponseHandler.handle_response(
                    response,
                    LoginResponse,
                    service_name="Authentication service"
                )

        except Exception as e:
            HTTPResponseHandler.handle_request_error(e, "Authentication service")

    async def register(self, user_data: RegisterRequest) -> RegisterResponse:
        """
        Registra un nuevo usuario en la API externa.

        Args:
            user_data: Datos del nuevo usuario

        Returns:
            RegisterResponse con access_token y datos del usuario

        Raises:
            HTTPException: Si el registro falla o hay error de conexión
        """
        url = f"{self.base_url}/auth/register/user"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=user_data.model_dump(mode='json', exclude_none=True)
                )

                return HTTPResponseHandler.handle_response(
                    response,
                    RegisterResponse,
                    service_name="Registration service"
                )

        except Exception as e:
            HTTPResponseHandler.handle_request_error(e, "Registration service")

    async def verify_token(self, token: str) -> VerifyTokenResponse:
        """
        Verifica un token en la API externa.

        Args:
            token: JWT token a verificar

        Returns:
            VerifyTokenResponse con datos del usuario si el token es válido

        Raises:
            HTTPException: Si el token es inválido o hay error de conexión
        """
        url = f"{self.base_url}/auth/verify-token"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    params={"token": token}
                )

                return HTTPResponseHandler.handle_response(
                    response,
                    VerifyTokenResponse,
                    service_name="Token verification service"
                )

        except Exception as e:
            HTTPResponseHandler.handle_request_error(e, "Token verification service")


# Instancia global del proveedor de autenticación
auth_provider = AuthProvider()

