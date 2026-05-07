"""
Router principal de la API v1.
Agrupa todos los endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, targets, audits, downloads, sitemaps, rich_results, structured_validations, ws_notifications


api_router = APIRouter()

# Incluir routers de endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(targets.router, tags=["Targets"])
api_router.include_router(audits.router, tags=["Auditorías"])
api_router.include_router(downloads.router, tags=["Descargas"])
api_router.include_router(sitemaps.router, tags=["Sitemaps"])
api_router.include_router(rich_results.router, tags=["Rich Results"])
api_router.include_router(structured_validations.router, tags=["Structured Validations"])
api_router.include_router(ws_notifications.router, tags=["WebSockets"])
