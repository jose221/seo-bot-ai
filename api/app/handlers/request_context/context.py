from contextvars import ContextVar
from typing import Optional
from starlette.requests import Request

# 1. Creamos la variable de contexto con un valor inicial de None.
#    Esta variable guardará el objeto Request para cada petición.
#    La hacemos opcional para que no dé error si se accede fuera de una petición.
request_context: ContextVar[Optional[Request]] = ContextVar("request_context", default=None)