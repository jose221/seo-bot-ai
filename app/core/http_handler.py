"""
Helper para manejo centralizado de respuestas HTTP de APIs externas.
Proporciona métodos estáticos para parsear respuestas y manejar errores de forma consistente.
"""
from typing import TypeVar, Type
from fastapi import HTTPException, status
import httpx
from pydantic import BaseModel, ValidationError


T = TypeVar('T', bound=BaseModel)


class HTTPResponseHandler:
    """
    Clase estática para manejo centralizado de respuestas HTTP.
    Evita duplicación de código en los servicios que consumen APIs externas.
    """

    @staticmethod
    def handle_response(
        response: httpx.Response,
        success_model: Type[T],
        service_name: str = "External service"
    ) -> T:
        """
        Maneja la respuesta HTTP de forma centralizada.

        Args:
            response: Respuesta de httpx
            success_model: Modelo Pydantic para parsear la respuesta exitosa
            service_name: Nombre del servicio para mensajes de error

        Returns:
            Instancia del modelo success_model parseada

        Raises:
            HTTPException: Con el código y mensaje apropiado según el status
        """
        # 2xx Success
        if 200 <= response.status_code < 300:
            try:
                return success_model(**response.json())
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing {service_name} response: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error parsing response: {str(e)}"
                )

        # 400 Bad Request
        elif response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request to {service_name}: {response.text}"
            )

        # 401 Unauthorized
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or unauthorized access"
            )

        # 403 Forbidden
        elif response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )

        # 404 Not Found
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        # 422 Validation Error
        elif response.status_code == 422:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Validation error in request data"
            )

        # 5xx Server Errors
        elif response.status_code >= 500:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{service_name} is experiencing issues"
            )

        # Otros códigos no manejados
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"{service_name} error: {response.text}"
            )

    @staticmethod
    def handle_request_error(error: Exception, service_name: str = "External service") -> None:
        """
        Maneja errores de conexión/timeout de forma centralizada.

        Args:
            error: Excepción capturada
            service_name: Nombre del servicio para el mensaje

        Raises:
            HTTPException: Con código 503 y mensaje apropiado
        """
        if isinstance(error, httpx.TimeoutException):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{service_name} is temporarily unavailable (timeout)"
            )
        elif isinstance(error, httpx.RequestError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{service_name} is temporarily unavailable: {str(error)}"
            )
        else:
            # Re-lanzar si es HTTPException (ya fue manejada)
            if isinstance(error, HTTPException):
                raise error
            # Cualquier otra excepción
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error communicating with {service_name}: {str(error)}"
            )

