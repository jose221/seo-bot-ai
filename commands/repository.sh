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

# ============ DETECCIÓN DE MODELS Y SERVICE ============
echo ""
echo "${BLUE}🔍 Buscando models y service relacionados...${NC}"

# Rutas de búsqueda
MODELS_REQUEST_PATH="${BASE_PATH}/domain/models/${directory_name}/request"
MODELS_RESPONSE_PATH="${BASE_PATH}/domain/models/${directory_name}/response"
MODELS_SIMPLE_PATH="${BASE_PATH}/domain/models/${directory_name}"
SERVICE_PATH="${BASE_PATH}/infrastructure/services/${directory_name}"
SERVICE_FILE="${SERVICE_PATH}/${file_name}.service.ts"

# Detectar tipo de models
has_models=false
has_request_response=false
model_files=()

if [[ -d "$MODELS_REQUEST_PATH" ]] || [[ -d "$MODELS_RESPONSE_PATH" ]]; then
    has_request_response=true
    has_models=true
    echo "${CYAN}✓ Detectados models con Request/Response${NC}"

    # Listar archivos de models
    if [[ -d "$MODELS_REQUEST_PATH" ]]; then
        for file in "$MODELS_REQUEST_PATH"/*.model.ts; do
            if [[ -f "$file" ]]; then
                model_files+=("$file")
            fi
        done
    fi
    if [[ -d "$MODELS_RESPONSE_PATH" ]]; then
        for file in "$MODELS_RESPONSE_PATH"/*.model.ts; do
            if [[ -f "$file" ]]; then
                model_files+=("$file")
            fi
        done
    fi
elif [[ -f "${MODELS_SIMPLE_PATH}/${file_name}.model.ts" ]]; then
    has_models=true
    echo "${CYAN}✓ Detectado model simple${NC}"
    model_files+=("${MODELS_SIMPLE_PATH}/${file_name}.model.ts")
else
    echo "${YELLOW}ℹ No se detectaron models para ${file_name}${NC}"
fi

# Detectar service
has_service=false
service_methods=()

if [[ -f "$SERVICE_FILE" ]]; then
    has_service=true
    echo "${CYAN}✓ Detectado service: ${file_name}.service.ts${NC}"

    # Extraer métodos del service usando Python
    service_methods=($(python3 -c "$(cat << 'PYEOF'
import sys
import re

service_file = sys.argv[1]
with open(service_file, 'r') as f:
    content = f.read()

# Buscar métodos async públicos
pattern = r'async\s+(\w+)\s*\([^)]*\)\s*:\s*Promise<([^>]+)>'
matches = re.findall(pattern, content)

for method_name, return_type in matches:
    if not method_name.startswith('_'):  # Ignorar métodos privados
        print(f"{method_name}:{return_type}")
PYEOF
)" "$SERVICE_FILE"))

    if [[ ${#service_methods[@]} -gt 0 ]]; then
        echo "${CYAN}  → Métodos detectados: ${#service_methods[@]}${NC}"
        for method in "${service_methods[@]}"; do
            method_name="${method%%:*}"
            echo "${CYAN}    • ${method_name}()${NC}"
        done
    fi
else
    echo "${YELLOW}ℹ No se detectó service para ${file_name}${NC}"
fi

# Preguntar si desea agregar el service al repository
add_service_to_repo=false
if [[ "$has_service" == true ]] && [[ ${#service_methods[@]} -gt 0 ]]; then
    echo ""
    echo "${YELLOW}❓ ¿Quieres que agregue el servicio detectado al repository? (s/n):${NC}"
    read -r add_service_response

    if [[ "$add_service_response" == "s" || "$add_service_response" == "S" ]]; then
        add_service_to_repo=true
    fi
fi

# Regenerar archivos con service si se confirmó
if [[ "$add_service_to_repo" == true ]]; then
    echo ""
    echo "${BLUE}🔄 Regenerando archivos con integración de service...${NC}"

    # Extraer información completa de los métodos
    python3 << 'PYEOF' "$SERVICE_FILE" "$DOMAIN_FILE" "$INFRA_FILE" "$class_name" "$file_name" "$directory_name"
import sys
import re

service_file = sys.argv[1]
domain_file = sys.argv[2]
infra_file = sys.argv[3]
class_name = sys.argv[4]
file_name = sys.argv[5]
directory_name = sys.argv[6]

# Leer el service
with open(service_file, 'r') as f:
    service_content = f.read()

# Extraer imports de models del service
model_imports = set()
import_pattern = r'import\s*{([^}]+)}\s*from\s*[\'"]@/app/domain/models/([^\'"]+)[\'"];'
for match in re.finditer(import_pattern, service_content):
    imports = match.group(1).strip()
    path = match.group(2).strip()
    model_imports.add(f"import {{{imports}}} from '@/app/domain/models/{path}';")

# Extraer métodos con sus parámetros y tipos de retorno
method_pattern = r'async\s+(\w+)\s*\(([^)]*)\)\s*:\s*Promise<([^>]+)>\s*{'
methods = []

for match in re.finditer(method_pattern, service_content):
    method_name = match.group(1)
    params = match.group(2).strip()
    return_type = match.group(3).strip()

    if not method_name.startswith('_'):  # Ignorar métodos privados
        methods.append({
            'name': method_name,
            'params': params,
            'return_type': return_type
        })

# Generar domain repository (interface)
domain_content = []
domain_content.append("// Imports de models")
for import_line in sorted(model_imports):
    domain_content.append(import_line)
domain_content.append("")
domain_content.append(f"export abstract class {class_name} {{")

for method in methods:
    domain_content.append(f"  abstract {method['name']}({method['params']}): Promise<{method['return_type']}>;")

domain_content.append("}")

# Escribir domain repository
with open(domain_file, 'w') as f:
    f.write('\n'.join(domain_content))

# Generar implementation repository
impl_class_name = class_name.replace('Repository', 'ImplementationRepository')
impl_content = []
impl_content.append("import { Injectable } from '@angular/core';")
impl_content.append(f"import {{{class_name}}} from '@/app/domain/repositories/{directory_name}/{file_name}.repository';")

for import_line in sorted(model_imports):
    impl_content.append(import_line)

impl_content.append(f"import {{{class_name.replace('Repository', 'Service')}}} from '@/app/infrastructure/services/{directory_name}/{file_name}.service';")
impl_content.append("")
impl_content.append("@Injectable({")
impl_content.append("  providedIn: 'root'")
impl_content.append("})")
impl_content.append(f"export class {impl_class_name} implements {class_name} {{")
impl_content.append(f"  constructor(private primaryService: {class_name.replace('Repository', 'Service')}) {{")
impl_content.append("")
impl_content.append("  }")

for method in methods:
    impl_content.append(f"  async {method['name']}({method['params']}): Promise<{method['return_type']}> {{")
    impl_content.append(f"    return await this.primaryService.{method['name']}({method['params'].split(':')[0].strip() if ':' in method['params'] else ''});")
    impl_content.append("  }")

impl_content.append("}")

# Escribir implementation repository
with open(infra_file, 'w') as f:
    f.write('\n'.join(impl_content))

print(f"✓ Archivos actualizados con {len(methods)} métodos")
PYEOF

    echo "${GREEN}✓ Archivos regenerados con métodos del service${NC}"
fi

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

