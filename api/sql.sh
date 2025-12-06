#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# migration.sh (menu)
# PostgreSQL helper para:
#   - Crear/actualizar estructura (bd/tables.sql)
#   - Sembrar datos de desarrollo (bd/seerder.sql)
#   - Reset completo (drop schemas + up + seed)
#   - Backup a bd/migration.sql
#   - Restore desde bd/migration.sql
#
# Requisitos: psql, createdb, pg_dump
# ==============================================================================

# ---------- Config ----------
# Revisa si el primer argumento es --prod
if [ "${1:-}" == "--prod" ]; then
    # --- CONFIGURACIÓN DE PRODUCCIÓN ---
    echo "Estas en producción"
    IS_PROD=true
    DB_HOST="84.247.137.97"
    # ¡IMPORTANTE! Rellena las demás credenciales de producción aquí
    DB_PORT="5432"
    DB_USER="herandro"
    DB_PASSWORD="Gonzales220"
    DB_NAME="seo_bot_db"
else
    # --- CONFIGURACIÓN LOCAL (por defecto) ---
    IS_PROD=false
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_USER="herandro"
    DB_PASSWORD="Gonzales220"
    DB_NAME="seo_bot_db"
fi

# Archivos (siempre en carpeta bd/)
TABLES_FILE="bd/tables.sql"
SEED_FILE="bd/seeder.sql"
BACKUP_FILE="bd/migration.sql"

SCHEMAS=("core" "rbac" "authn" "credits" "ai" "billing" "audit")

# Colores
C_RESET="\033[0m"
C_BLUE="\033[1;34m"
C_GREEN="\033[1;32m"
C_YELLOW="\033[1;33m"
C_RED="\033[1;31m"
C_GRAY="\033[0;37m"

# pgpass temporal
PGPASSFILE="$(mktemp)"
cleanup() { rm -f "$PGPASSFILE"; }
trap cleanup EXIT
echo "${DB_HOST}:${DB_PORT}:${DB_NAME}:${DB_USER}:${DB_PASSWORD}" > "$PGPASSFILE"
chmod 600 "$PGPASSFILE"
export PGPASSFILE

PSQL=(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v "ON_ERROR_STOP=1" -q)
CREATEDB=(createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER")
PG_DUMP=(pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F p)

# ---------- Helpers ----------
pause() { read -rp $'\nPresiona ENTER para continuar...'; }

header() {
  echo -e "${C_BLUE}\n==> $*${C_RESET}"
}

info()    { echo -e "${C_GRAY}$*${C_RESET}"; }
ok()      { echo -e "${C_GREEN}$*${C_RESET}"; }
warn()    { echo -e "${C_YELLOW}$*${C_RESET}"; }
err()     { echo -e "${C_RED}$*${C_RESET}"; }

ensure_db() {
  if ! "${PSQL[@]}" -c "SELECT 1;" >/dev/null 2>&1; then
    warn "BD ${DB_NAME} no existe o no accesible. Intentando crear..."
    "${CREATEDB[@]}" "$DB_NAME" 2>/dev/null || true
  fi
}

check_file() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    err "No se encontró el archivo requerido: $f"
    return 1
  fi
}

show_config() {
  header "Configuración actual"
  cat <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

ARCHIVOS:
  tables.sql : ${TABLES_FILE}
  seerder.sql: ${SEED_FILE}
  backup     : ${BACKUP_FILE}
EOF
}

apply_tables() {
  header "Aplicar estructura (${TABLES_FILE})"
  ensure_db
  check_file "$TABLES_FILE" || return 1
  "${PSQL[@]}" -f "$TABLES_FILE"
  ok "Estructura aplicada."
}

seed_data() {
  header "Sembrar datos de desarrollo (${SEED_FILE})"
  ensure_db
  check_file "$SEED_FILE" || return 1
  "${PSQL[@]}" -f "$SEED_FILE"
  ok "Seed aplicado."
}

drop_schemas() {
  header "Drop de schemas y tipos personalizados"
  ensure_db

  # Eliminar schemas
  for schema in "${SCHEMAS[@]}"; do
    info "Eliminando schema: ${schema}"
    "${PSQL[@]}" -c "DROP SCHEMA IF EXISTS ${schema} CASCADE;" 2>/dev/null || true
  done

  # Eliminar tipos personalizados (ENUMs) que puedan quedar
  info "Eliminando tipos personalizados..."
  "${PSQL[@]}" <<SQL 2>/dev/null || true
DO \$\$
DECLARE
    r RECORD;
BEGIN
    -- Eliminar todos los tipos personalizados (excepto los del sistema)
    FOR r IN (
        SELECT typname
        FROM pg_type t
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        AND t.typtype = 'e'  -- Solo ENUMs
    ) LOOP
        EXECUTE format('DROP TYPE IF EXISTS %I CASCADE;', r.typname);
    END LOOP;
END
\$\$;
SQL

  ok "Schemas y tipos eliminados."
}

reset_all() {
  header "RESET COMPLETO"
  warn "Esto eliminará schemas y datos de los módulos: ${SCHEMAS[*]}"
  read -rp "¿Seguro? (escribe YES para continuar): " yn
  if [[ "$yn" != "YES" ]]; then
    warn "Abortado."
    return 0
  fi
  drop_schemas
  apply_tables
  seed_data
  ok "Reset completado."
}

backup_db() {
  header "Backup a ${BACKUP_FILE}"
  ensure_db
  mkdir -p bd
  "${PG_DUMP[@]}" > "${BACKUP_FILE}"
  ok "Backup guardado en ${BACKUP_FILE}"
}

restore_db() {
  header "Restore de schemas desde ${BACKUP_FILE}"
  ensure_db
  check_file "$BACKUP_FILE" || return 1
  warn "Esto aplicará el contenido de ${BACKUP_FILE} sobre los schemas de ${DB_NAME}."
  warn "Se eliminarán los schemas: ${SCHEMAS[*]} y luego se restaurarán."
  read -rp "¿Continuar con la restauración de schemas? (escribe YES para continuar): " yn
  if [[ "$yn" != "YES" ]]; then
    warn "Abortado."
    return 0
  fi

  # Primero eliminar schemas existentes
  drop_schemas

  # Luego restaurar desde el backup (sin ON_ERROR_STOP para que continúe con warnings)
  info "Restaurando schemas desde backup..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -f "${BACKUP_FILE}" 2>/dev/null || true

  ok "Restauración de schemas aplicada (algunos warnings son normales)."
}

restore_db_full() {
  header "Restore COMPLETO (recrear base de datos)"
  check_file "$BACKUP_FILE" || return 1
  warn "Esto ELIMINARÁ y RECREARÁ la base de datos completa: ${DB_NAME}"
  warn "Se perderán TODOS los datos de TODA la base de datos."
  read -rp "¿Continuar con recreación completa? (escribe YES para continuar): " yn
  if [[ "$yn" != "YES" ]]; then
    warn "Abortado."
    return 0
  fi

  info "Terminando conexiones activas..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<SQL 2>/dev/null || true
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
SQL

  info "Eliminando base de datos..."
  dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$DB_NAME" 2>/dev/null || true

  info "Recreando base de datos..."
  "${CREATEDB[@]}" "$DB_NAME"

  info "Restaurando desde backup (ignorando errores de tipos existentes)..."
  if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -f "${BACKUP_FILE}"; then
    err "Ocurrió un error durante la restauración. Revisa los mensajes anteriores."
  fi

  ok "Restauración completa finalizada (algunos warnings son normales)."
}

# ---------- Menú ----------
menu() {
  clear
  echo -e "${C_BLUE}Herandro Postgres Manager${C_RESET}"
  echo -e "${C_GRAY}(${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME})${C_RESET}\n"
  echo "1) Mostrar configuración actual"
  echo "2) Probar conexión"
  echo "------------------------------"
  echo "3) Aplicar estructura (bd/tables.sql)"
  echo "4) Sembrar datos (bd/seerder.sql)"
  echo "5) RESET (drop schemas + up + seed)"
  echo "------------------------------"
  echo "6) RESTORE schemas <- bd/migration.sql"
  echo "7) RESTORE completo (recrear BD) <- bd/migration.sql"
  echo "8) Backup -> bd/migration.sql"
  echo "0) Salir"
  echo
}

main_loop() {
  while true; do
    menu
    read -rp "Selecciona una opción: " op
    case "${op:-}" in
      1) show_config; pause ;;
      2) "${PSQL[@]}" -c "SELECT version();" && ok "Conexión OK."; pause ;;
      3) apply_tables; pause ;;
      4) seed_data; pause ;;
      5) reset_all; pause ;;
      6) restore_db; pause ;;
      7) restore_db_full; pause ;;
      8) backup_db; pause ;;
      0) echo "Adiós!"; break ;;
      *) warn "Opción no válida"; pause ;;
    esac
  done
}

main_loop