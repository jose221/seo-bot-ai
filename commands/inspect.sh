#!/bin/zsh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║     Inspector de Módulos - SEO Bot AI         ║${NC}"
echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# Solicitar el nombre del módulo
echo "${YELLOW}📁 Ingresa el nombre del módulo a inspeccionar:${NC}"
read -r module_name

if [[ -z "$module_name" ]]; then
    echo "${RED}❌ Error: El nombre del módulo no puede estar vacío${NC}"
    exit 1
fi

BASE_PATH="/Users/joseangelalvaradogonzalez/seo-bot-ai/src/app"

echo ""
echo "${CYAN}═══════════ Inspeccionando: ${module_name} ═══════════${NC}"
echo ""

# Función para listar archivos con detalles
list_files_in_dir() {
    local dir=$1
    local label=$2

    if [[ -d "$dir" ]]; then
        local file_count=$(find "$dir" -type f -name "*.ts" 2>/dev/null | wc -l | tr -d ' ')

        if [[ $file_count -gt 0 ]]; then
            echo "${GREEN}✓ ${label} (${file_count} archivos)${NC}"

            for file in "$dir"/**/*.ts(N); do
                if [[ -f "$file" ]]; then
                    local filename=$(basename "$file")
                    local filesize=$(stat -f%z "$file" 2>/dev/null || echo "0")
                    local lines=$(wc -l < "$file" 2>/dev/null | tr -d ' ')

                    echo "  ${CYAN}→${NC} ${filename} ${YELLOW}(${lines} líneas)${NC}"

                    # Extraer clases/interfaces/exports del archivo
                    local exports=$(grep -E "^export (class|interface|abstract class|const|function)" "$file" 2>/dev/null | sed 's/export //' | cut -d'{' -f1 | cut -d'(' -f1)

                    if [[ -n "$exports" ]]; then
                        while IFS= read -r export_line; do
                            echo "    ${BLUE}•${NC} ${export_line}"
                        done <<< "$exports"
                    fi
                fi
            done
            echo ""
        else
            echo "${YELLOW}○ ${label} (vacío)${NC}"
        fi
    else
        echo "${RED}✗ ${label} (no existe)${NC}"
    fi
}

# Inspeccionar Domain Layer
echo "${YELLOW}Domain Layer:${NC}"
list_files_in_dir "${BASE_PATH}/domain/models/${module_name}" "  Models"
list_files_in_dir "${BASE_PATH}/domain/repositories/${module_name}" "  Repositories"
list_files_in_dir "${BASE_PATH}/domain/mappers/${module_name}" "  Mappers"

# Inspeccionar Infrastructure Layer
echo "${YELLOW}Infrastructure Layer:${NC}"
list_files_in_dir "${BASE_PATH}/infrastructure/services/${module_name}" "  Services"
list_files_in_dir "${BASE_PATH}/infrastructure/repositories/${module_name}" "  Repository Implementations"

# Buscar DTOs relacionados
echo "${YELLOW}DTOs:${NC}"
if [[ -d "${BASE_PATH}/infrastructure/dto" ]]; then
    dto_files=$(find "${BASE_PATH}/infrastructure/dto" -type f -name "*${module_name}*.dto.ts" 2>/dev/null)

    if [[ -n "$dto_files" ]]; then
        echo "${GREEN}✓ DTOs encontrados${NC}"
        while IFS= read -r dto_file; do
            if [[ -f "$dto_file" ]]; then
                filename=$(basename "$dto_file")
                lines=$(wc -l < "$dto_file" 2>/dev/null | tr -d ' ')
                echo "  ${CYAN}→${NC} ${filename} ${YELLOW}(${lines} líneas)${NC}"
            fi
        done <<< "$dto_files"
        echo ""
    else
        echo "${YELLOW}○ No se encontraron DTOs para ${module_name}${NC}"
    fi
else
    echo "${RED}✗ Directorio de DTOs no existe${NC}"
fi

# Inspeccionar Application Layer
echo "${YELLOW}Application Layer:${NC}"
list_files_in_dir "${BASE_PATH}/application/use-cases/${module_name}" "  Use Cases"

# Buscar en app.config.ts
echo "${YELLOW}Configuración:${NC}"
CONFIG_FILE="${BASE_PATH}/app.config.ts"
if [[ -f "$CONFIG_FILE" ]]; then
    providers=$(grep -i "${module_name}" "$CONFIG_FILE" 2>/dev/null | grep "provide:")

    if [[ -n "$providers" ]]; then
        echo "${GREEN}✓ Providers registrados en app.config.ts${NC}"
        while IFS= read -r provider; do
            echo "  ${CYAN}→${NC} ${provider}"
        done <<< "$providers"
    else
        echo "${YELLOW}○ No se encontraron providers en app.config.ts${NC}"
    fi
else
    echo "${RED}✗ app.config.ts no encontrado${NC}"
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║           ✓ Inspección completada              ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""

