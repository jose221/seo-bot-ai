"""
Aplicación principal de FastAPI - SEO Bot AI
Inicialización de la aplicación, configuración de CORS y routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de ciclo de vida de la aplicación.
    Se ejecuta al inicio y al cierre de la aplicación.
    """
    # Inicializar base de datos (solo si está disponible)
    try:
        print("🚀 Inicializando base de datos...")
        await init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"⚠️  Base de datos no disponible: {e}")
        print("⚠️  La aplicación continuará sin persistencia")

    yield

    print("👋 Cerrando aplicación...")


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de auditoría web inteligente con IA",
    lifespan=lifespan
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir routers
app.include_router(api_router, prefix="/api/v1")

# Configurar Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "message": "SEO Bot AI - Sistema de auditoría web inteligente"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint para verificar el estado del servicio"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }

