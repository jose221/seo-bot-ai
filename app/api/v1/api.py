"""
Router principal de la API v1.
Agrupa todos los endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth


api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(auth.router, prefix="/auth")

