#!/bin/zsh

# Colores para el menú
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║       Generador de Models - SEO Bot AI        ║${NC}"
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
echo "${GREEN}✓ Clase base: ${class_name}${NC}"
echo ""

# Preguntar si quiere request
echo "${YELLOW}❓ ¿Quieres que sea Request? (s/n):${NC}"
read -r wants_request

# Preguntar si quiere response (solo si confirmó request)
wants_response="n"
if [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
    echo "${YELLOW}❓ ¿Quieres el Response? (s/n):${NC}"
    read -r wants_response
fi

# Preguntar si quiere DTOs
echo "${YELLOW}❓ ¿Quieres los DTO? (s/n):${NC}"
read -r wants_dto

# Preguntar si quiere mapper (solo si confirmó DTOs)
wants_mapper="n"
if [[ "$wants_dto" == "s" || "$wants_dto" == "S" ]]; then
    echo "${YELLOW}❓ ¿Quieres el Mapper? (s/n):${NC}"
    read -r wants_mapper
fi

echo ""
echo "${CYAN}═══════════════════ RESUMEN ═══════════════════${NC}"
if [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
    echo "${GREEN}✓ Request: Sí${NC}"
else
    echo "${GREEN}✓ Request: No${NC}"
fi
if [[ "$wants_response" == "s" || "$wants_response" == "S" ]]; then
    echo "${GREEN}✓ Response: Sí${NC}"
else
    echo "${GREEN}✓ Response: No${NC}"
fi
if [[ "$wants_dto" == "s" || "$wants_dto" == "S" ]]; then
    echo "${GREEN}✓ DTO: Sí${NC}"
else
    echo "${GREEN}✓ DTO: No${NC}"
fi
if [[ "$wants_mapper" == "s" || "$wants_mapper" == "S" ]]; then
    echo "${GREEN}✓ Mapper: Sí${NC}"
else
    echo "${GREEN}✓ Mapper: No${NC}"
fi
echo "${CYAN}══════════════════════════════════════════════${NC}"
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
DOMAIN_MODELS_PATH="${BASE_PATH}/domain/models/${directory_name}"
INFRA_DTO_PATH="${BASE_PATH}/infrastructure/dto"
MAPPER_PATH="${BASE_PATH}/domain/mappers/${directory_name}"

echo ""
echo "${BLUE}🚀 Creando archivos...${NC}"

# Variables para almacenar rutas de archivos creados
created_files=()

# ============ CREAR MODELS ============
if [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
    # Crear Request Model
    REQUEST_MODEL_PATH="${DOMAIN_MODELS_PATH}/request"
    mkdir -p "$REQUEST_MODEL_PATH"

    REQUEST_MODEL_FILE="${REQUEST_MODEL_PATH}/${file_name}-request.model.ts"
    cat > "$REQUEST_MODEL_FILE" << EOF
export class ${class_name}RequestModel {
  constructor(

  ) {
  }
}
EOF
    echo "${GREEN}✓ Creado: ${REQUEST_MODEL_FILE}${NC}"
    created_files+=("$REQUEST_MODEL_FILE")

    # Crear Response Model si lo confirmó
    if [[ "$wants_response" == "s" || "$wants_response" == "S" ]]; then
        RESPONSE_MODEL_PATH="${DOMAIN_MODELS_PATH}/response"
        mkdir -p "$RESPONSE_MODEL_PATH"

        RESPONSE_MODEL_FILE="${RESPONSE_MODEL_PATH}/${file_name}-response.model.ts"
        cat > "$RESPONSE_MODEL_FILE" << EOF
export class ${class_name}ResponseModel {
  constructor(
  ) {}
}
EOF
        echo "${GREEN}✓ Creado: ${RESPONSE_MODEL_FILE}${NC}"
        created_files+=("$RESPONSE_MODEL_FILE")
    fi
else
    # Crear Model simple (sin request/response)
    mkdir -p "$DOMAIN_MODELS_PATH"

    MODEL_FILE="${DOMAIN_MODELS_PATH}/${file_name}.model.ts"
    cat > "$MODEL_FILE" << EOF
export class ${class_name}Model {
  constructor(
  ) {}
}
EOF
    echo "${GREEN}✓ Creado: ${MODEL_FILE}${NC}"
    created_files+=("$MODEL_FILE")
fi

# ============ CREAR DTOs ============
if [[ "$wants_dto" == "s" || "$wants_dto" == "S" ]]; then
    if [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
        # Crear Request DTO
        REQUEST_DTO_PATH="${INFRA_DTO_PATH}/request"
        mkdir -p "$REQUEST_DTO_PATH"

        REQUEST_DTO_FILE="${REQUEST_DTO_PATH}/${file_name}-request.dto.ts"
        cat > "$REQUEST_DTO_FILE" << EOF
export interface ${class_name}RequestDto {

}
EOF
        echo "${GREEN}✓ Creado: ${REQUEST_DTO_FILE}${NC}"
        created_files+=("$REQUEST_DTO_FILE")

        # Crear Response DTO si lo confirmó
        if [[ "$wants_response" == "s" || "$wants_response" == "S" ]]; then
            RESPONSE_DTO_PATH="${INFRA_DTO_PATH}/response"
            mkdir -p "$RESPONSE_DTO_PATH"

            RESPONSE_DTO_FILE="${RESPONSE_DTO_PATH}/${file_name}-response.dto.ts"
            cat > "$RESPONSE_DTO_FILE" << EOF
export interface ${class_name}ResponseDto {

}
EOF
            echo "${GREEN}✓ Creado: ${RESPONSE_DTO_FILE}${NC}"
            created_files+=("$RESPONSE_DTO_FILE")
        fi
    else
        # Crear DTO simple (sin request/response)
        mkdir -p "$INFRA_DTO_PATH"

        DTO_FILE="${INFRA_DTO_PATH}/${file_name}.dto.ts"
        cat > "$DTO_FILE" << EOF
export interface ${class_name}Dto {

}
EOF
        echo "${GREEN}✓ Creado: ${DTO_FILE}${NC}"
        created_files+=("$DTO_FILE")
    fi
fi

# ============ CREAR MAPPER ============
if [[ "$wants_mapper" == "s" || "$wants_mapper" == "S" ]]; then
    mkdir -p "$MAPPER_PATH"

    MAPPER_FILE="${MAPPER_PATH}/${file_name}.mapper.ts"

    # Generar imports según la configuración
    mapper_imports=""

    if [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
        # Con Request
        mapper_imports+="import {${class_name}RequestDto} from '@/app/infrastructure/dto/request/${file_name}-request.dto';\n"
        mapper_imports+="import {${class_name}RequestModel} from '@/app/domain/models/${directory_name}/request/${file_name}-request.model';\n"

        if [[ "$wants_response" == "s" || "$wants_response" == "S" ]]; then
            # Con Request y Response
            mapper_imports+="import {${class_name}ResponseDto} from '@/app/infrastructure/dto/response/${file_name}-response.dto';\n"
            mapper_imports+="import {${class_name}ResponseModel} from '@/app/domain/models/${directory_name}/response/${file_name}-response.model';\n"
        fi
    else
        # Sin Request ni Response
        mapper_imports+="import {${class_name}Dto} from '@/app/infrastructure/dto/${file_name}.dto';\n"
        mapper_imports+="import {${class_name}Model} from '@/app/domain/models/${directory_name}/${file_name}.model';\n"
    fi

    # Generar contenido del mapper según la configuración
    if [[ "$wants_request" == "s" || "$wants_request" == "S" ]] && [[ "$wants_response" == "s" || "$wants_response" == "S" ]]; then
        # Con Request y Response
        {
            echo "import { AppMapper } from \"../app.mapper\";"
            echo -e "${mapper_imports}"
            echo ""
            echo "export class ${class_name}Mapper extends AppMapper {"
            echo "  constructor() {"
            echo "    super();"
            echo "  }"
            echo "  // --------- mapRequest (sobrecargas)"
            echo "  mapRequest(dto: ${class_name}RequestDto): ${class_name}RequestModel;"
            echo "  mapRequest(model: ${class_name}RequestModel): ${class_name}RequestDto;"
            echo "  mapRequest(input: ${class_name}RequestDto | ${class_name}RequestModel) {"
            echo "    return this.autoMap<any, any>(input, { except: [] });"
            echo "  }"
            echo "  "
            echo "  // --------- mapResponse (sobrecargas)"
            echo "  mapResponse(dto: ${class_name}ResponseDto): ${class_name}ResponseModel;"
            echo "  mapResponse(model: ${class_name}ResponseModel): ${class_name}ResponseDto;"
            echo "  mapResponse(input: ${class_name}ResponseDto | ${class_name}ResponseModel) {"
            echo "    return this.autoMap<any, any>(input, { except: [] });"
            echo "  }"
            echo "}"
        } > "$MAPPER_FILE"
    elif [[ "$wants_request" == "s" || "$wants_request" == "S" ]]; then
        # Solo Request
        {
            echo "import { AppMapper } from \"../app.mapper\";"
            echo -e "${mapper_imports}"
            echo ""
            echo "export class ${class_name}Mapper extends AppMapper {"
            echo "  constructor() {"
            echo "    super();"
            echo "  }"
            echo "  // --------- mapRequest (sobrecargas)"
            echo "  mapRequest(dto: ${class_name}RequestDto): ${class_name}RequestModel;"
            echo "  mapRequest(model: ${class_name}RequestModel): ${class_name}RequestDto;"
            echo "  mapRequest(input: ${class_name}RequestDto | ${class_name}RequestModel) {"
            echo "    return this.autoMap<any, any>(input, { except: [] });"
            echo "  }"
            echo "  "
            echo "}"
        } > "$MAPPER_FILE"
    else
        # Sin Request ni Response (map genérico)
        {
            echo "import { AppMapper } from \"../app.mapper\";"
            echo -e "${mapper_imports}"
            echo ""
            echo "export class ${class_name}Mapper extends AppMapper {"
            echo "  constructor() {"
            echo "    super();"
            echo "  }"
            echo "  // --------- map (sobrecargas)"
            echo "  map(dto: ${class_name}Dto): ${class_name}Model;"
            echo "  map(model: ${class_name}Model): ${class_name}Dto;"
            echo "  map(input: ${class_name}Dto | ${class_name}Model) {"
            echo "    return this.autoMap<any, any>(input, { except: [] });"
            echo "  }"
            echo ""
            echo ""
            echo "}"
        } > "$MAPPER_FILE"
    fi

    echo "${GREEN}✓ Creado: ${MAPPER_FILE}${NC}"
    created_files+=("$MAPPER_FILE")
fi

echo ""
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║            ✓ Proceso completado                ║${NC}"
echo "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo "${BLUE}Archivos creados:${NC}"
for file in "${created_files[@]}"; do
    echo "  → ${file}"
done
echo ""

