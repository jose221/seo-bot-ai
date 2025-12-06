#!/bin/bash
set -e

# Iniciar Xvfb (Virtual Display) en background
echo "🖥️  Starting Xvfb virtual display..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Esperar a que Xvfb esté listo
sleep 2

echo "✅ Xvfb started on DISPLAY=:99 (PID: $XVFB_PID)"

# Ejecutar el comando principal (uvicorn)
exec "$@"

