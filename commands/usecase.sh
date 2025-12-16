#!/bin/zsh

# Colores para el menú
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║      Generador de Use Cases - SEO Bot AI      ║${NC}"
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
echo "${YELLOW}📄 Ingresa el nombre del caso de uso (ej: login, register, get-user):${NC}"
read -r file_name

# Validar que no esté vacío
if [[ -z "$file_name" ]]; then
    echo "${RED}❌ Error: El nombre del caso de uso no puede estar vacío${NC}"
    exit 1
fi

# Generar el nombre de la clase automáticamente (convertir kebab-case a PascalCase)
class_name=$(echo "$file_name" | awk -F'-' '{for(i=1;i<=NF;i++) printf "%s", toupper(substr($i,1,1)) tolower(substr($i,2))}')
class_name="${class_name}UseCase"

echo ""
echo "${GREEN}✓ Directorio: ${directory_name}${NC}"
echo "${GREEN}✓ Archivo: ${file_name}${NC}"
echo "${GREEN}✓ Clase: ${class_name}${NC}"
echo ""

# Rutas base
BASE_PATH="/Users/joseangelalvaradogonzalez/seo-bot-ai/src/app"
USECASE_PATH="${BASE_PATH}/application/use-cases/${directory_name}"
REPOSITORY_PATH="${BASE_PATH}/domain/repositories/${directory_name}"

# Buscar repositorios relacionados
echo "${BLUE}🔍 Buscando repositorios relacionados...${NC}"
repository_files=()
if [[ -d "$REPOSITORY_PATH" ]]; then
    for file in "$REPOSITORY_PATH"/*.repository.ts; do
        if [[ -f "$file" ]]; then
            repository_files+=("$file")
            echo "${CYAN}✓ Detectado: $(basename "$file")${NC}"
        fi
    done
fi

if [[ ${#repository_files[@]} -eq 0 ]]; then
    echo "${YELLOW}⚠️  No se detectaron repositorios para ${directory_name}${NC}"
    echo "${YELLOW}   El use case se creará sin dependencias de repositorio${NC}"
fi

echo ""
echo "${YELLOW}¿Deseas continuar con esta configuración? (s/n):${NC}"
read -r confirm

if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    echo "${RED}❌ Operación cancelada${NC}"
    exit 0
fi

echo ""
echo "${BLUE}🚀 Creando Use Case...${NC}"

# Crear directorio si no existe
mkdir -p "$USECASE_PATH"

# Crear archivo de use case
USECASE_FILE="${USECASE_PATH}/${file_name}.use-case.ts"

# Generar contenido basado en si hay repositorios
if [[ ${#repository_files[@]} -gt 0 ]]; then
    # Extraer información del primer repositorio encontrado
    first_repo_file="${repository_files[0]}"
    repo_basename=$(basename "$first_repo_file" .repository.ts)
    repo_class_name="$(capitalize "$repo_basename")Repository"

    cat > "$USECASE_FILE" << EOF
import { Injectable } from '@angular/core';
import {${repo_class_name}} from '@/app/domain/repositories/${directory_name}/${repo_basename}.repository';

@Injectable({
  providedIn: 'root'
})
export class ${class_name} {
  constructor(
    private ${repo_basename}Repository: ${repo_class_name}
  ) {}

  async execute(params?: any): Promise<any> {
    // TODO: Implementar lógica del caso de uso
    throw new Error('Use case not implemented');
  }
}
EOF

    echo "${GREEN}✓ Use case creado con repositorio: ${repo_class_name}${NC}"
else
    # Sin repositorios
    cat > "$USECASE_FILE" << EOF
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ${class_name} {
  constructor() {}

  async execute(params?: any): Promise<any> {
    // TODO: Implementar lógica del caso de uso
    throw new Error('Use case not implemented');
  }
}
EOF

    echo "${GREEN}✓ Use case creado sin dependencias${NC}"
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║            ✓ Proceso completado                ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo "${BLUE}Archivo creado:${NC}"
echo "  → ${USECASE_FILE}"
echo ""

