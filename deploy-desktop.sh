#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/api"
DESKTOP_VENV_DIR="$API_DIR/.desktop-python"
PYTHON_BIN="$DESKTOP_VENV_DIR/bin/python3"
PLAYWRIGHT_BIN="$DESKTOP_VENV_DIR/bin/playwright"
OUTPUT_DIR="$ROOT_DIR/release/desktop"
DESKTOP_DROP_DIR="$HOME/Desktop/SEO-Bot-AI-Desktop"
DESKTOP_APP_PATH="$DESKTOP_DROP_DIR/mac-arm64/SEO Bot AI.app"
BASE_PYTHON_BIN="${SEO_BOT_DESKTOP_PYTHON:-}"
DEBUG_MODE=0

for arg in "$@"; do
  case "$arg" in
    --debug)
      DEBUG_MODE=1
      ;;
    *)
      fail "Argumento no soportado: $arg"
      ;;
  esac
done

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

fail() {
  printf '\n[ERROR] %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "No encontre el comando requerido: $1"
}

log "Validando prerequisitos"
require_cmd node
require_cmd npm
require_cmd rsync

if [[ -z "$BASE_PYTHON_BIN" ]]; then
  if command -v python3.13 >/dev/null 2>&1; then
    BASE_PYTHON_BIN="$(command -v python3.13)"
  else
    BASE_PYTHON_BIN="$(command -v python3)"
  fi
fi

[[ -x "$BASE_PYTHON_BIN" ]] || fail "No encontre un interprete Python valido para desktop"

[[ -f "$ROOT_DIR/package.json" ]] || fail "No encontre package.json en $ROOT_DIR"
[[ -f "$API_DIR/requirements.txt" ]] || fail "No encontre api/requirements.txt"
[[ -f "$API_DIR/.env" ]] || fail "No encontre api/.env. El backend de escritorio lo necesita."

NODE_VERSION="$(node -p 'process.versions.node')"
if ! node -e "const [major, minor] = process.versions.node.split('.').map(Number); process.exit(major > 20 || (major === 20 && minor >= 19) ? 0 : 1)"; then
  log "Aviso: Node $NODE_VERSION esta por debajo de 20.19.0. El build puede fallar por engines de Angular/Electron."
fi

cd "$ROOT_DIR"

log "Instalando dependencias Node"
npm install

log "Preparando entorno Python para desktop en $DESKTOP_VENV_DIR con $BASE_PYTHON_BIN"
rm -rf "$DESKTOP_VENV_DIR"
"$BASE_PYTHON_BIN" -m venv --copies "$DESKTOP_VENV_DIR"

log "Actualizando pip/setuptools/wheel"
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

log "Instalando dependencias Python del backend"
PLAYWRIGHT_BROWSERS_PATH=0 "$PYTHON_BIN" -m pip install -r "$API_DIR/requirements.txt"

log "Instalando Chromium de Playwright dentro del paquete"
PLAYWRIGHT_BROWSERS_PATH=0 "$PLAYWRIGHT_BIN" install chromium

log "Compilando Angular para escritorio"
npm run build:desktop:web

log "Empaquetando app de Electron"
rm -rf "$OUTPUT_DIR"
npx electron-builder --mac dmg --publish never --config.directories.output="$OUTPUT_DIR"

mkdir -p "$DESKTOP_DROP_DIR"
log "Copiando artefactos al Escritorio en $DESKTOP_DROP_DIR"
rsync -a --delete "$OUTPUT_DIR/" "$DESKTOP_DROP_DIR/"

[[ -d "$DESKTOP_APP_PATH" ]] || fail "No encontre la app empaquetada en $DESKTOP_APP_PATH"

log "Abriendo la app empaquetada"
if [[ "$DEBUG_MODE" -eq 1 ]]; then
  open "$DESKTOP_APP_PATH" --args --auth-debug
else
  open "$DESKTOP_APP_PATH"
fi

log "Deploy terminado"
printf 'Artefactos disponibles en:\n- %s\n' "$DESKTOP_DROP_DIR"
if [[ "$DEBUG_MODE" -eq 1 ]]; then
  printf 'Log de auth/debug:\n- %s\n' "$HOME/Desktop/seo-bot-ai-auth-debug.log"
fi
