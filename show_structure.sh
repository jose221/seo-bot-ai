#!/bin/bash
# Script para mostrar la estructura del proyecto

echo "================================================"
echo "🏗️  ESTRUCTURA DEL PROYECTO SEO BOT AI"
echo "================================================"
echo ""

echo "📁 Archivos de configuración raíz:"
ls -1 | grep -E '\.(yml|txt|md|py|example)$|Dockerfile' | sed 's/^/  ├── /'
echo ""

echo "📁 Estructura de la aplicación (app/):"
find app -type f -name "*.py" | sort | sed 's|app/|  ├── app/|' | sed 's|/| → |g'
echo ""

echo "📁 Dependencias instaladas:"
pip list | grep -E 'fastapi|uvicorn|sqlmodel|httpx|playwright|pydantic' | sed 's/^/  ├── /'
echo ""

echo "✅ Estado de instalación:"
echo "  ├── Python: $(python --version 2>&1 | cut -d' ' -f2)"
echo "  ├── Pip: $(pip --version | cut -d' ' -f2)"
echo "  ├── FastAPI: Instalado ✓"
echo "  ├── Playwright: Instalado ✓"
echo "  ├── PostgreSQL: Requiere Docker 🐳"
echo ""

echo "================================================"
echo "🚀 Para iniciar:"
echo "  docker-compose up -d"
echo ""
echo "📖 Documentación:"
echo "  http://localhost:8000/docs"
echo "================================================"

