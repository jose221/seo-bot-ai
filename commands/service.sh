#!/bin/zsh

# Colores para el menú
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║      Generador de Services - SEO Bot AI       ║${NC}"
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
class_name="$(capitalize "$file_name")"

echo ""
echo "${GREEN}✓ Directorio: ${directory_name}${NC}"
echo "${GREEN}✓ Archivo: ${file_name}${NC}"
echo "${GREEN}✓ Clase: ${class_name}Service${NC}"
echo ""

# Rutas base
BASE_PATH="/Users/joseangelalvaradogonzalez/seo-bot-ai/src/app"
SERVICE_PATH="${BASE_PATH}/infrastructure/services/${directory_name}"
MAPPER_PATH="${BASE_PATH}/domain/mappers/${directory_name}"

# Verificar si existe el mapper
MAPPER_FILE="${MAPPER_PATH}/${file_name}.mapper.ts"
has_mapper=false

if [[ -f "$MAPPER_FILE" ]]; then
    has_mapper=true
    echo "${CYAN}✓ Se detectó mapper existente: ${file_name}.mapper.ts${NC}"
    echo "${CYAN}  → Se importará automáticamente en el servicio${NC}"
else
    echo "${YELLOW}ℹ No se detectó mapper para ${file_name}${NC}"
    echo "${YELLOW}  → El servicio se creará sin mapper${NC}"
fi

echo ""

# Confirmar
echo "${YELLOW}¿Deseas continuar con esta configuración? (s/n):${NC}"
read -r confirm

if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    echo "${RED}❌ Operación cancelada${NC}"
    exit 0
fi

echo ""
echo "${BLUE}🚀 Creando servicio...${NC}"

# Crear directorio si no existe
mkdir -p "$SERVICE_PATH"

# Crear archivo de servicio
SERVICE_FILE="${SERVICE_PATH}/${file_name}.service.ts"

# Generar contenido del servicio según si existe mapper o no
if [[ "$has_mapper" == true ]]; then
    # Con mapper
    cat > "$SERVICE_FILE" << EOF
import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {${class_name}Mapper} from '@/app/domain/mappers/${directory_name}/${file_name}.mapper';

@Injectable({
  providedIn: 'root'
})
export class ${class_name}Service {
  itemMapper = new ${class_name}Mapper();
  constructor(private httpService: HttpService) {
  }
}
EOF
    echo "${GREEN}✓ Creado: ${SERVICE_FILE} (con mapper)${NC}"
else
    # Sin mapper
    cat > "$SERVICE_FILE" << EOF
import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';

@Injectable({
  providedIn: 'root'
})
export class ${class_name}Service {
  constructor(private httpService: HttpService) {
  }
}
EOF
    echo "${GREEN}✓ Creado: ${SERVICE_FILE}${NC}"
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║            ✓ Proceso completado                ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo "${BLUE}Archivo creado:${NC}"
echo "  → ${SERVICE_FILE}"
if [[ "$has_mapper" == true ]]; then
    echo ""
    echo "${CYAN}Mapper detectado e importado:${NC}"
    echo "  → ${MAPPER_FILE}"
fi
echo ""

