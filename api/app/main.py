"""
Aplicación principal de FastAPI - SEO Bot AI
Inicialización de la aplicación, configuración de CORS y routers.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import RequestResponseEndpoint

from app.core.config import settings
from app.core.database import init_db
from app.core.security import clear_request_auth_context
from app.api.v1.api import api_router
from app.shared.herandro_services_api.herandro_services_api_client import (
    close_hsa_client,
    init_hsa_client,
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de ciclo de vida de la aplicación.
    Se ejecuta al inicio y al cierre de la aplicación.
    """
    # 1. Base de datos
    try:
        print("🚀 Inicializando base de datos...")
        await init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"⚠️  Base de datos no disponible: {e}")
        print("⚠️  La aplicación continuará sin persistencia")

    # 2. Cliente Herandro Services API
    await init_hsa_client(
        base_url=settings.HSA_BASE_URL,
        timeout=settings.HSA_TIMEOUT_SECONDS,
    )
    print(f"✅ Herandro Services API client inicializado → {settings.HSA_BASE_URL}")

    yield

    # Limpieza
    await close_hsa_client()
    print("👋 Cerrando aplicación...")


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Sistema de auditoría web inteligente con IA\n\n"
        "**Autenticación:** Bearer JWT de Keycloak."
    ),
    lifespan=lifespan,
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware que limpia el contexto de autenticación por request
@app.middleware("http")
async def request_auth_context_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    clear_request_auth_context()
    try:
        return await call_next(request)
    finally:
        clear_request_auth_context()


# Incluir routers
app.include_router(api_router, prefix="/api/v1")

# Montar directorio de storage para servir archivos estáticos
storage_path = settings.STORAGE_PATH
if not os.path.exists(storage_path):
    try:
        os.makedirs(storage_path, exist_ok=True)
        print(f"📁 Directorio creado: {storage_path}")
    except OSError as e:
        print(f"⚠️ No se pudo crear {storage_path}: {e}")

if os.path.exists(storage_path):
    app.mount(settings.STORAGE_URL_PREFIX, StaticFiles(directory=storage_path), name="storage")
    print(f"✅ Storage montado en {settings.STORAGE_URL_PREFIX} -> {storage_path}")
else:
    print(f"❌ Storage NO disponible en {storage_path}")

# Configurar Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "message": "SEO Bot AI - Sistema de auditoría web inteligente",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
    }


