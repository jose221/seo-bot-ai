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

# Verificar si existen carpetas request/response
REQUEST_PATH="${BASE_PATH}/domain/models/${directory_name}/request"
RESPONSE_PATH="${BASE_PATH}/domain/models/${directory_name}/response"
DTO_REQUEST_PATH="${BASE_PATH}/infrastructure/dto/request"
DTO_RESPONSE_PATH="${BASE_PATH}/infrastructure/dto/response"

has_request=false
has_response=false

if [[ -d "$REQUEST_PATH" ]]; then
    has_request=true
fi

if [[ -d "$RESPONSE_PATH" ]]; then
    has_response=true
fi

# Preguntar si desea agregar operaciones CRUD
echo "${YELLOW}¿Deseas agregar operaciones CRUD básicas? (s/n):${NC}"
read -r add_crud

if [[ "$add_crud" == "s" || "$add_crud" == "S" ]]; then
    echo ""
    echo "${BLUE}🔧 Configurando operaciones CRUD...${NC}"
    echo ""

    # Arrays para almacenar las operaciones seleccionadas
    operations=()

    # Preguntar por cada operación
    echo "${YELLOW}¿Agregar CREATE? (s/n):${NC}"
    read -r add_create
    [[ "$add_create" == "s" || "$add_create" == "S" ]] && operations+=("create")

    echo "${YELLOW}¿Agregar UPDATE? (s/n):${NC}"
    read -r add_update
    [[ "$add_update" == "s" || "$add_update" == "S" ]] && operations+=("update")

    echo "${YELLOW}¿Agregar DELETE? (s/n):${NC}"
    read -r add_delete
    [[ "$add_delete" == "s" || "$add_delete" == "S" ]] && operations+=("delete")

    echo "${YELLOW}¿Agregar GET (lista)? (s/n):${NC}"
    read -r add_get
    [[ "$add_get" == "s" || "$add_get" == "S" ]] && operations+=("get")

    echo "${YELLOW}¿Agregar FIND (por id)? (s/n):${NC}"
    read -r add_find
    [[ "$add_find" == "s" || "$add_find" == "S" ]] && operations+=("find")

    if [[ ${#operations[@]} -gt 0 ]]; then
        echo ""
        echo "${BLUE}🔨 Generando operaciones CRUD...${NC}"

        # Crear/actualizar DTOs y Models según las operaciones
        for op in "${operations[@]}"; do
            case "$op" in
                "create"|"update")
                    if [[ "$has_request" == true ]]; then
                        # Crear clase en request DTO
                        op_capitalized="$(capitalize "$op")"
                        dto_class="${op_capitalized}${class_name}RequestDto"
                        model_class="${op_capitalized}${class_name}RequestModel"

                        # Agregar a DTO request
                        DTO_REQUEST_FILE="${DTO_REQUEST_PATH}/${file_name}-request.dto.ts"
                        if [[ -f "$DTO_REQUEST_FILE" ]]; then
                            # Verificar si la clase ya existe
                            if ! grep -q "export interface ${dto_class}" "$DTO_REQUEST_FILE"; then
                                echo "" >> "$DTO_REQUEST_FILE"
                                echo "export interface ${dto_class} {" >> "$DTO_REQUEST_FILE"
                                echo "}" >> "$DTO_REQUEST_FILE"
                                echo "${GREEN}  ✓ Agregado ${dto_class} a ${file_name}-request.dto.ts${NC}"
                            fi
                        else
                            echo "export interface ${dto_class} {" > "$DTO_REQUEST_FILE"
                            echo "}" >> "$DTO_REQUEST_FILE"
                            echo "${GREEN}  ✓ Creado ${file_name}-request.dto.ts con ${dto_class}${NC}"
                        fi

                        # Agregar a Model request
                        MODEL_REQUEST_FILE="${REQUEST_PATH}/${file_name}-request.model.ts"
                        if [[ -f "$MODEL_REQUEST_FILE" ]]; then
                            if ! grep -q "export class ${model_class}" "$MODEL_REQUEST_FILE"; then
                                echo "" >> "$MODEL_REQUEST_FILE"
                                echo "export class ${model_class} {" >> "$MODEL_REQUEST_FILE"
                                echo "  constructor(" >> "$MODEL_REQUEST_FILE"
                                echo "  ) {" >> "$MODEL_REQUEST_FILE"
                                echo "  }" >> "$MODEL_REQUEST_FILE"
                                echo "}" >> "$MODEL_REQUEST_FILE"
                                echo "${GREEN}  ✓ Agregado ${model_class} a ${file_name}-request.model.ts${NC}"
                            fi
                        else
                            echo "export class ${model_class} {" > "$MODEL_REQUEST_FILE"
                            echo "  constructor(" >> "$MODEL_REQUEST_FILE"
                            echo "  ) {" >> "$MODEL_REQUEST_FILE"
                            echo "  }" >> "$MODEL_REQUEST_FILE"
                            echo "}" >> "$MODEL_REQUEST_FILE"
                            echo "${GREEN}  ✓ Creado ${file_name}-request.model.ts con ${model_class}${NC}"
                        fi

                        # Actualizar mapper si existe
                        if [[ "$has_mapper" == true ]]; then
                            # Agregar imports al mapper si no existen
                            if ! grep -q "import.*${dto_class}" "$MAPPER_FILE"; then
                                sed -i '' "1i\\
import {${dto_class}} from '@/app/infrastructure/dto/request/${file_name}-request.dto';\\
" "$MAPPER_FILE"
                            fi
                            if ! grep -q "import.*${model_class}" "$MAPPER_FILE"; then
                                sed -i '' "1i\\
import {${model_class}} from '@/app/domain/models/${directory_name}/request/${file_name}-request.model';\\
" "$MAPPER_FILE"
                            fi

                            # Agregar método map al mapper si no existe
                            if ! grep -q "map${op_capitalized}" "$MAPPER_FILE"; then
                                # Insertar antes del último }
                                sed -i '' '$d' "$MAPPER_FILE"
                                cat >> "$MAPPER_FILE" << EOF

  // --------- map${op_capitalized} (sobrecargas)
  map${op_capitalized}(dto: ${dto_class}): ${model_class};
  map${op_capitalized}(model: ${model_class}): ${dto_class};
  map${op_capitalized}(input: ${dto_class} | ${model_class}) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
EOF
                                echo "${GREEN}  ✓ Agregado map${op_capitalized} al mapper${NC}"
                            fi
                        fi
                    fi
                    ;;
                "get"|"find")
                    if [[ "$has_response" == true ]]; then
                        # Verificar que existan los archivos base de response
                        dto_class="${class_name}ResponseDto"
                        model_class="${class_name}ResponseModel"

                        DTO_RESPONSE_FILE="${DTO_RESPONSE_PATH}/${file_name}-response.dto.ts"
                        if [[ ! -f "$DTO_RESPONSE_FILE" ]]; then
                            echo "export interface ${dto_class} {" > "$DTO_RESPONSE_FILE"
                            echo "}" >> "$DTO_RESPONSE_FILE"
                            echo "${GREEN}  ✓ Creado ${file_name}-response.dto.ts${NC}"
                        fi

                        MODEL_RESPONSE_FILE="${RESPONSE_PATH}/${file_name}-response.model.ts"
                        if [[ ! -f "$MODEL_RESPONSE_FILE" ]]; then
                            echo "export class ${model_class} {" > "$MODEL_RESPONSE_FILE"
                            echo "  constructor(" >> "$MODEL_RESPONSE_FILE"
                            echo "  ) {}" >> "$MODEL_RESPONSE_FILE"
                            echo "}" >> "$MODEL_RESPONSE_FILE"
                            echo "${GREEN}  ✓ Creado ${file_name}-response.model.ts${NC}"
                        fi
                    fi
                    ;;
            esac
        done

        # Para operación GET, crear FilterModel si existe request
        if [[ " ${operations[@]} " =~ " get " ]] && [[ "$has_request" == true ]]; then
            filter_dto_class="Filter${class_name}RequestDto"
            filter_model_class="Filter${class_name}RequestModel"

            DTO_REQUEST_FILE="${DTO_REQUEST_PATH}/${file_name}-request.dto.ts"
            if [[ -f "$DTO_REQUEST_FILE" ]]; then
                if ! grep -q "export interface ${filter_dto_class}" "$DTO_REQUEST_FILE"; then
                    echo "" >> "$DTO_REQUEST_FILE"
                    echo "export interface ${filter_dto_class} {" >> "$DTO_REQUEST_FILE"
                    echo "}" >> "$DTO_REQUEST_FILE"
                    echo "${GREEN}  ✓ Agregado ${filter_dto_class} a ${file_name}-request.dto.ts${NC}"
                fi
            fi

            MODEL_REQUEST_FILE="${REQUEST_PATH}/${file_name}-request.model.ts"
            if [[ -f "$MODEL_REQUEST_FILE" ]]; then
                if ! grep -q "export class ${filter_model_class}" "$MODEL_REQUEST_FILE"; then
                    echo "" >> "$MODEL_REQUEST_FILE"
                    echo "export class ${filter_model_class} {" >> "$MODEL_REQUEST_FILE"
                    echo "  constructor(" >> "$MODEL_REQUEST_FILE"
                    echo "  ) {" >> "$MODEL_REQUEST_FILE"
                    echo "  }" >> "$MODEL_REQUEST_FILE"
                    echo "}" >> "$MODEL_REQUEST_FILE"
                    echo "${GREEN}  ✓ Agregado ${filter_model_class} a ${file_name}-request.model.ts${NC}"
                fi
            fi

            # Actualizar mapper
            if [[ "$has_mapper" == true ]]; then
                if ! grep -q "import.*${filter_dto_class}" "$MAPPER_FILE"; then
                    sed -i '' "1i\\
import {${filter_dto_class}} from '@/app/infrastructure/dto/request/${file_name}-request.dto';\\
" "$MAPPER_FILE"
                fi
                if ! grep -q "import.*${filter_model_class}" "$MAPPER_FILE"; then
                    sed -i '' "1i\\
import {${filter_model_class}} from '@/app/domain/models/${directory_name}/request/${file_name}-request.model';\\
" "$MAPPER_FILE"
                fi

                if ! grep -q "mapFilter" "$MAPPER_FILE"; then
                    sed -i '' '$d' "$MAPPER_FILE"
                    cat >> "$MAPPER_FILE" << EOF

  // --------- mapFilter (sobrecargas)
  mapFilter(dto: ${filter_dto_class}): ${filter_model_class};
  mapFilter(model: ${filter_model_class}): ${filter_dto_class};
  mapFilter(input: ${filter_dto_class} | ${filter_model_class}) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
EOF
                    echo "${GREEN}  ✓ Agregado mapFilter al mapper${NC}"
                fi
            fi
        fi

        # Generar métodos en el servicio
        echo ""
        echo "${BLUE}📝 Agregando métodos al servicio...${NC}"

        # Preparar imports usando arrays para evitar duplicados
        declare -a request_model_imports=()
        declare -a response_model_imports=()
        declare -a response_dto_imports=()
        add_http_helper=false

        # Recolectar imports necesarios
        for op in "${operations[@]}"; do
            case "$op" in
                "create")
                    [[ "$has_request" == true ]] && request_model_imports+=("Create${class_name}RequestModel")
                    ;;
                "update")
                    [[ "$has_request" == true ]] && request_model_imports+=("Update${class_name}RequestModel")
                    ;;
                "get")
                    [[ "$has_request" == true ]] && request_model_imports+=("Filter${class_name}RequestModel")
                    if [[ "$has_response" == true ]]; then
                        response_model_imports+=("${class_name}ResponseModel")
                        response_dto_imports+=("${class_name}ResponseDto")
                    fi
                    add_http_helper=true
                    ;;
                "find")
                    if [[ "$has_response" == true ]]; then
                        response_model_imports+=("${class_name}ResponseModel")
                        response_dto_imports+=("${class_name}ResponseDto")
                    fi
                    ;;
            esac
        done

        # Eliminar duplicados manualmente
        request_model_imports=($(printf '%s\n' "${request_model_imports[@]}" | sort -u))
        response_model_imports=($(printf '%s\n' "${response_model_imports[@]}" | sort -u))
        response_dto_imports=($(printf '%s\n' "${response_dto_imports[@]}" | sort -u))

        # Construir líneas de import
        import_lines=""

        # Import de request models
        if [[ ${#request_model_imports[@]} -gt 0 ]]; then
            import_str=$(IFS=', '; echo "${request_model_imports[*]}")
            import_lines="${import_lines}import {${import_str}} from '@/app/domain/models/${directory_name}/request/${file_name}-request.model';\n"
        fi

        # Import de response models
        if [[ ${#response_model_imports[@]} -gt 0 ]]; then
            import_str=$(IFS=', '; echo "${response_model_imports[*]}")
            import_lines="${import_lines}import {${import_str}} from '@/app/domain/models/${directory_name}/response/${file_name}-response.model';\n"
        fi

        # Import de response dtos
        if [[ ${#response_dto_imports[@]} -gt 0 ]]; then
            import_str=$(IFS=', '; echo "${response_dto_imports[*]}")
            import_lines="${import_lines}import {${import_str}} from '@/app/infrastructure/dto/response/${file_name}-response.dto';\n"
        fi

        # Import de HttpClientHelper
        if [[ "$add_http_helper" == true ]]; then
            import_lines="${import_lines}import {HttpClientHelper} from '@/app/helper/http-client.helper';\n"
        fi

        # Insertar imports en el servicio
        if [[ -n "$import_lines" ]]; then
            # Insertar después del último import existente
            last_import_line=$(grep -n "^import" "$SERVICE_FILE" | tail -1 | cut -d: -f1)
            if [[ -n "$last_import_line" ]]; then
                # Crear archivo temporal con los imports agregados
                head -n "$last_import_line" "$SERVICE_FILE" > "${SERVICE_FILE}.tmp"
                echo -e "$import_lines" >> "${SERVICE_FILE}.tmp"
                tail -n +$((last_import_line + 1)) "$SERVICE_FILE" >> "${SERVICE_FILE}.tmp"
                mv "${SERVICE_FILE}.tmp" "$SERVICE_FILE"
            fi
        fi

        # Generar métodos - escribir directamente al archivo
        # Eliminar el último } del archivo para agregar métodos
        sed -i '' '$d' "$SERVICE_FILE"

        for op in "${operations[@]}"; do
            case "$op" in
                "create")
                    if [[ "$has_request" == true ]]; then
                        param_type="Create${class_name}RequestModel"
                        mapper_call="this.itemMapper.mapCreate(params)"
                    else
                        param_type="any"
                        mapper_call="params"
                    fi

                    cat >> "$SERVICE_FILE" << EOF

  async create(params: ${param_type}): Promise<any> {
    return await this.httpService.post<any>('', ${mapper_call});
  }
EOF
                    ;;
                "update")
                    if [[ "$has_request" == true ]]; then
                        param_type="Update${class_name}RequestModel"
                        mapper_call="this.itemMapper.mapUpdate(params)"
                    else
                        param_type="any"
                        mapper_call="params"
                    fi

                    cat >> "$SERVICE_FILE" << EOF

  async update(params: ${param_type}): Promise<any> {
    return await this.httpService.put<any>('', ${mapper_call});
  }
EOF
                    ;;
                "get")
                    if [[ "$has_request" == true ]]; then
                        param_type="Filter${class_name}RequestModel"
                        mapper_call="params ? this.itemMapper.mapFilter(params) : ''"
                    else
                        param_type="any"
                        mapper_call="params"
                    fi

                    if [[ "$has_response" == true ]]; then
                        return_type="${class_name}ResponseModel[]"
                        dto_type="${class_name}ResponseDto[]"
                        cat >> "$SERVICE_FILE" << EOF

  async get(params?: ${param_type}): Promise<${return_type}> {
    let nParams = params ? HttpClientHelper.objectToQueryString(${mapper_call}) : '';
    const response = await this.httpService.get<${dto_type}>('?' + nParams);
    return response.map(item => this.itemMapper.mapResponse(item));
  }
EOF
                    else
                        return_type="any"
                        dto_type="any"
                        cat >> "$SERVICE_FILE" << EOF

  async get(params?: ${param_type}): Promise<${return_type}> {
    let nParams = params ? HttpClientHelper.objectToQueryString(${mapper_call}) : '';
    const response = await this.httpService.get<${dto_type}>('?' + nParams);
    return response;
  }
EOF
                    fi
                    ;;
                "find")
                    if [[ "$has_response" == true ]]; then
                        return_type="${class_name}ResponseModel"
                        dto_type="${class_name}ResponseDto"
                        cat >> "$SERVICE_FILE" << EOF

  async find(id: number): Promise<${return_type}> {
    const response = await this.httpService.get<${dto_type}>('/' + id);
    return this.itemMapper.mapResponse(response);
  }
EOF
                    else
                        return_type="any"
                        dto_type="any"
                        cat >> "$SERVICE_FILE" << EOF

  async find(id: number): Promise<${return_type}> {
    const response = await this.httpService.get<${dto_type}>('/' + id);
    return response;
  }
EOF
                    fi
                    ;;
                "delete")
                    cat >> "$SERVICE_FILE" << EOF

  async delete(id: number): Promise<any> {
    return await this.httpService.delete<any>('/' + id);
  }
EOF
                    ;;
            esac
        done

        # Cerrar la clase
        echo "}" >> "$SERVICE_FILE"
        echo "${GREEN}  ✓ Métodos CRUD agregados al servicio${NC}"

        echo ""
        echo "${GREEN}✓ Operaciones CRUD configuradas exitosamente${NC}"
    fi
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

