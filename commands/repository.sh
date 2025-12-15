#!/bin/zsh

# Colores para el menú
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║     Generador de Repository - SEO Bot AI      ║${NC}"
echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# Función para capitalizar primera letra
capitalize() {
    echo "$1" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2));}1'
}

# Solicitar el nombre del directorio
echo "${YELLOW}📁 Ingresa el nombre del directorio (ej: auth, user, product):${NC}"
read -r directory_name

# Validar que no esté vacío
if [[ -z "$directory_name" ]]; then
    echo "${RED}❌ Error: El nombre del directorio no puede estar vacío${NC}"
    exit 1
fi

# Solicitar el nombre del archivo
echo "${YELLOW}📄 Ingresa el nombre del archivo (ej: auth, user, product):${NC}"
read -r file_name

# Validar que no esté vacío
if [[ -z "$file_name" ]]; then
    echo "${RED}❌ Error: El nombre del archivo no puede estar vacío${NC}"
    exit 1
fi

# Generar el nombre de la clase automáticamente
class_name="$(capitalize "$file_name")Repository"

echo ""
echo "${GREEN}✓ Directorio: ${directory_name}${NC}"
echo "${GREEN}✓ Archivo: ${file_name}${NC}"
echo "${GREEN}✓ Clase: ${class_name}${NC}"
echo ""

# Confirmar
echo "${YELLOW}¿Deseas continuar con esta configuración? (s/n):${NC}"
read -r confirm

if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    echo "${RED}❌ Operación cancelada${NC}"
    exit 0
fi

# Rutas base
BASE_PATH="/Users/joseangelalvaradogonzalez/seo-bot-ai/src/app"
DOMAIN_PATH="${BASE_PATH}/domain/repositories/${directory_name}"
INFRA_PATH="${BASE_PATH}/infrastructure/repositories/${directory_name}"
CONFIG_FILE="${BASE_PATH}/app.config.ts"

echo ""
echo "${BLUE}🚀 Creando archivos...${NC}"

# Crear directorio domain si no existe
mkdir -p "$DOMAIN_PATH"

# Crear archivo de repositorio en domain
DOMAIN_FILE="${DOMAIN_PATH}/${file_name}.repository.ts"
cat > "$DOMAIN_FILE" << EOF
export abstract class ${class_name} {

}
EOF

echo "${GREEN}✓ Creado: ${DOMAIN_FILE}${NC}"

# Crear directorio infrastructure si no existe
mkdir -p "$INFRA_PATH"

# Crear archivo de implementación en infrastructure
INFRA_FILE="${INFRA_PATH}/${file_name}.implementation.repository.ts"
cat > "$INFRA_FILE" << EOF
import { Injectable } from '@angular/core';
import {${class_name}} from '@/app/domain/repositories/${directory_name}/${file_name}.repository';

@Injectable({
  providedIn: 'root'
})
export class ${class_name/Repository/ImplementationRepository} implements ${class_name} {
  constructor() {

  }
}
EOF

echo "${GREEN}✓ Creado: ${INFRA_FILE}${NC}"

# Actualizar app.config.ts
echo ""
echo "${BLUE}📝 Actualizando app.config.ts...${NC}"

# Obtener el nombre de la clase de implementación
IMPL_CLASS_NAME="${class_name/Repository/ImplementationRepository}"

# Crear los imports
DOMAIN_IMPORT="import {${class_name}} from '@/app/domain/repositories/${directory_name}/${file_name}.repository';"
INFRA_IMPORT="import {${IMPL_CLASS_NAME}} from '@/app/infrastructure/repositories/${directory_name}/${file_name}.implementation.repository';"

# Verificar si los imports ya existen
if grep -q "${class_name}" "$CONFIG_FILE" && grep -q "${IMPL_CLASS_NAME}" "$CONFIG_FILE"; then
    echo "${YELLOW}⚠ Los imports del repositorio ya existen en app.config.ts${NC}"
else
    # Usar Python para actualizar el archivo de forma segura
    python3 -c "$(cat << 'EOF'
import sys
with open(sys.argv[1], 'r') as f:
    content = f.read()
lines = content.split('\n')
last_import_index = -1
for i, line in enumerate(lines):
    if line.startswith('import') and 'from' in line:
        last_import_index = i
if last_import_index != -1:
    lines.insert(last_import_index + 1, sys.argv[3])
    lines.insert(last_import_index + 1, sys.argv[2])
with open(sys.argv[1], 'w') as f:
    f.write('\n'.join(lines))
EOF
)" "$CONFIG_FILE" "$DOMAIN_IMPORT" "$INFRA_IMPORT"

    echo "${GREEN}✓ Imports agregados${NC}"
fi

# Verificar si el provider ya existe
PROVIDER_LINE="{ provide: ${class_name}, useClass: ${IMPL_CLASS_NAME} }"

if grep -q "provide: ${class_name}" "$CONFIG_FILE"; then
    echo "${YELLOW}⚠ El provider ya existe en app.config.ts${NC}"
else
    # Usar Python para agregar el provider
    python3 -c "$(cat << 'EOF'
import sys
with open(sys.argv[1], 'r') as f:
    content = f.read()
lines = content.split('\n')
last_provider_index = -1
for i, line in enumerate(lines):
    if 'provide:' in line and 'useClass:' in line:
        last_provider_index = i
if last_provider_index != -1:
    if not lines[last_provider_index].rstrip().endswith(','):
        lines[last_provider_index] = lines[last_provider_index].rstrip() + ','
    lines.insert(last_provider_index + 1, '    ' + sys.argv[2])
with open(sys.argv[1], 'w') as f:
    f.write('\n'.join(lines))
EOF
)" "$CONFIG_FILE" "$PROVIDER_LINE"

    echo "${GREEN}✓ Provider agregado${NC}"
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║            ✓ Proceso completado                ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo "${BLUE}Archivos creados:${NC}"
echo "  → ${DOMAIN_FILE}"
echo "  → ${INFRA_FILE}"
echo ""
echo "${BLUE}Configuración actualizada:${NC}"
echo "  → ${CONFIG_FILE}"
echo ""

