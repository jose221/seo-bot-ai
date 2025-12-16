#!/bin/zsh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║     Validador de Estructura - SEO Bot AI      ║${NC}"
echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

BASE_PATH="/Users/joseangelalvaradogonzalez/seo-bot-ai/src/app"

# Función para verificar directorios
check_directory() {
    local dir=$1
    local name=$2
    if [[ -d "$dir" ]]; then
        echo "${GREEN}✓${NC} ${name}"
        return 0
    else
        echo "${RED}✗${NC} ${name} ${YELLOW}(no existe)${NC}"
        return 1
    fi
}

# Función para contar archivos
count_files() {
    local dir=$1
    local pattern=$2
    if [[ -d "$dir" ]]; then
        find "$dir" -name "$pattern" 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

echo "${CYAN}═══ Estructura de Capas ═══${NC}"
echo ""

# Domain Layer
echo "${YELLOW}Domain Layer:${NC}"
check_directory "${BASE_PATH}/domain" "  domain/"
check_directory "${BASE_PATH}/domain/models" "    ├── models/"
check_directory "${BASE_PATH}/domain/repositories" "    ├── repositories/"
check_directory "${BASE_PATH}/domain/mappers" "    ├── mappers/"

# Infrastructure Layer
echo ""
echo "${YELLOW}Infrastructure Layer:${NC}"
check_directory "${BASE_PATH}/infrastructure" "  infrastructure/"
check_directory "${BASE_PATH}/infrastructure/dto" "    ├── dto/"
check_directory "${BASE_PATH}/infrastructure/repositories" "    ├── repositories/"
check_directory "${BASE_PATH}/infrastructure/services" "    ├── services/"

# Application Layer
echo ""
echo "${YELLOW}Application Layer:${NC}"
check_directory "${BASE_PATH}/application" "  application/"
check_directory "${BASE_PATH}/application/use-cases" "    └── use-cases/"

echo ""
echo "${CYAN}═══ Estadísticas ═══${NC}"
echo ""

# Contar archivos por tipo
models_count=$(count_files "${BASE_PATH}/domain/models" "*.model.ts")
repos_count=$(count_files "${BASE_PATH}/domain/repositories" "*.repository.ts")
mappers_count=$(count_files "${BASE_PATH}/domain/mappers" "*.mapper.ts")
dtos_count=$(count_files "${BASE_PATH}/infrastructure/dto" "*.dto.ts")
services_count=$(count_files "${BASE_PATH}/infrastructure/services" "*.service.ts")
usecases_count=$(count_files "${BASE_PATH}/application/use-cases" "*.use-case.ts")

echo "📦 Modelos (Models):           ${GREEN}${models_count}${NC}"
echo "🗄️  Repositorios (Domain):      ${GREEN}${repos_count}${NC}"
echo "🔄 Mappers:                    ${GREEN}${mappers_count}${NC}"
echo "📋 DTOs:                       ${GREEN}${dtos_count}${NC}"
echo "🔧 Servicios:                  ${GREEN}${services_count}${NC}"
echo "⚡ Use Cases:                  ${GREEN}${usecases_count}${NC}"

echo ""
echo "${CYAN}═══ Módulos Detectados ═══${NC}"
echo ""

# Listar módulos en domain/models
if [[ -d "${BASE_PATH}/domain/models" ]]; then
    echo "${YELLOW}Módulos:${NC}"
    for dir in "${BASE_PATH}/domain/models"/*; do
        if [[ -d "$dir" ]]; then
            module_name=$(basename "$dir")

            # Verificar componentes del módulo
            has_model=false
            has_repo=false
            has_service=false
            has_dto=false
            has_mapper=false

            [[ $(count_files "$dir" "*.model.ts") -gt 0 ]] && has_model=true
            [[ $(count_files "${BASE_PATH}/domain/repositories/${module_name}" "*.repository.ts") -gt 0 ]] && has_repo=true
            [[ $(count_files "${BASE_PATH}/infrastructure/services/${module_name}" "*.service.ts") -gt 0 ]] && has_service=true
            [[ $(count_files "${BASE_PATH}/infrastructure/dto" "*${module_name}*.dto.ts") -gt 0 ]] && has_dto=true
            [[ $(count_files "${BASE_PATH}/domain/mappers/${module_name}" "*.mapper.ts") -gt 0 ]] && has_mapper=true

            echo -n "  ${CYAN}→ ${module_name}${NC}: "

            $has_model && echo -n "${GREEN}Model${NC} " || echo -n "${RED}Model${NC} "
            $has_dto && echo -n "${GREEN}DTO${NC} " || echo -n "${RED}DTO${NC} "
            $has_mapper && echo -n "${GREEN}Mapper${NC} " || echo -n "${RED}Mapper${NC} "
            $has_service && echo -n "${GREEN}Service${NC} " || echo -n "${RED}Service${NC} "
            $has_repo && echo -n "${GREEN}Repository${NC}" || echo -n "${RED}Repository${NC}"

            echo ""
        fi
    done
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║            ✓ Análisis completado               ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""

