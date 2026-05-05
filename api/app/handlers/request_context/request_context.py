from typing import Any, Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, Request
import json

from app.handlers.request_context import request_context


class RequestContext:
    """
    Clase estática para acceder a la información del request actual.
    No se debe instanciar.
    """
    def __init__(self):
        # Esto previene que alguien intente crear una instancia de la clase.
        raise TypeError("RequestContext es una clase estática y no puede ser instanciada.")

    @staticmethod
    def _get_request() -> Optional[Request]:
        """
        Método de ayuda interno para obtener de forma segura el request del contexto.
        """
        return request_context.get()

    @staticmethod
    def get_header(name: str, default: Optional[Any] = None) -> Optional[str]:
        """
        Obtiene un valor de las cabeceras (headers) del request actual.
        El nombre del header no distingue entre mayúsculas y minúsculas.

        :param name: El nombre del header (ej. "user-agent").
        :param default: Valor a devolver si el header no se encuentra.
        """
        request = RequestContext._get_request()
        if request:
            return request.headers.get(name, default)
        return default

    @staticmethod
    def get_body() -> bytes:
        """
        Obtiene el cuerpo (body) del request en formato de bytes.
        NOTA: Requiere que el middleware haya leído y guardado el body previamente.
        """
        request = RequestContext._get_request()
        # El middleware debe haber guardado el body en request.state.body
        if request and hasattr(request.state, "body"):
            return getattr(request.state, "body")
        return b""

    @staticmethod
    async def get_json() -> Any:
        """
        Obtiene el cuerpo (body) del request y lo decodifica como JSON.
        """
        body_bytes = RequestContext.get_body()
        if body_bytes:
            try:
                return json.loads(body_bytes)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @staticmethod
    def get_state(key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Obtiene un atributo guardado en el estado (state) del request.

        :param key: La clave del atributo a buscar.
        :param default: Valor por defecto si no se encuentra.
        """
        request = RequestContext._get_request()
        if request and hasattr(request.state, key):
            return getattr(request.state, key)
        return default

    @staticmethod
    def get_client_host() -> Optional[str]:
        """
        Obtiene la dirección IP del cliente.
        """
        request = RequestContext._get_request()
        if request and request.client:
            return request.client.host
        return None