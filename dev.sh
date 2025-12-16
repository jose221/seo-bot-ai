#!/bin/bash

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color

# Banner
show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              🚀 GENERADOR DE MÓDULOS - DEV                ║"
    echo "║                  Sistema de Arquitectura                  ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para mostrar el menú principal
show_main_menu() {
    echo -e "${YELLOW}┌─────────────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}│${NC}  Selecciona una opción:                             ${YELLOW}│${NC}"
    echo -e "${YELLOW}├─────────────────────────────────────────────────────┤${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}1.${NC} 📦 Crear Modelo (Model)                         ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}2.${NC} 🔧 Crear Servicio (Service)                     ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}3.${NC} 🗄️  Crear Repositorio (Repository)              ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}4.${NC} 🎯 Crear Módulo Completo                        ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}5.${NC} 🔄 Crear Use Case                               ${YELLOW}│${NC}"
    echo -e "${YELLOW}├─────────────────────────────────────────────────────┤${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}6.${NC} 📋 Ver Estructura del Proyecto                  ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}7.${NC} ✅ Validar Estructura                           ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}8.${NC} 🔍 Inspeccionar Módulo                          ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${GREEN}9.${NC} 🧹 Limpiar Módulo                               ${YELLOW}│${NC}"
    echo -e "${YELLOW}├─────────────────────────────────────────────────────┤${NC}"
    echo -e "${YELLOW}│${NC}  ${CYAN}?.${NC} 📚 Ayuda y Documentación                        ${YELLOW}│${NC}"
    echo -e "${YELLOW}│${NC}  ${RED}0.${NC} ❌ Salir                                         ${YELLOW}│${NC}"
    echo -e "${YELLOW}└─────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Función para crear modelo
create_model() {
    echo -e "${BLUE}📦 Ejecutando creación de Modelo...${NC}"
    bash "$(dirname "$0")/commands/model.sh"
}

# Función para crear servicio
create_service() {
    echo -e "${BLUE}🔧 Ejecutando creación de Servicio...${NC}"
    bash "$(dirname "$0")/commands/service.sh"
}

# Función para crear repositorio
create_repository() {
    echo -e "${BLUE}🗄️ Ejecutando creación de Repositorio...${NC}"
    bash "$(dirname "$0")/commands/repository.sh"
}

# Función para crear módulo completo
create_full_module() {
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║          🎯 CREACIÓN DE MÓDULO COMPLETO                   ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Este proceso creará:${NC}"
    echo -e "  ${GREEN}✓${NC} Modelos (Request/Response/Básico)"
    echo -e "  ${GREEN}✓${NC} DTOs"
    echo -e "  ${GREEN}✓${NC} Mappers"
    echo -e "  ${GREEN}✓${NC} Service"
    echo -e "  ${GREEN}✓${NC} Repository (Domain e Implementation)"
    echo ""

    echo -e "${YELLOW}Paso 1/3: Creando Modelos...${NC}"
    bash "$(dirname "$0")/commands/model.sh"

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${YELLOW}Paso 2/3: Creando Servicio...${NC}"
        bash "$(dirname "$0")/commands/service.sh"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${YELLOW}Paso 3/3: Creando Repositorio...${NC}"
            bash "$(dirname "$0")/commands/repository.sh"

            if [ $? -eq 0 ]; then
                echo ""
                echo -e "${GREEN}✅ ¡Módulo completo creado exitosamente!${NC}"
            fi
        fi
    fi
}

# Función para crear use case
create_use_case() {
    echo -e "${BLUE}🔄 Ejecutando creación de Use Case...${NC}"
    bash "$(dirname "$0")/commands/usecase.sh"
}

# Función para ver estructura
view_structure() {
    echo -e "${CYAN}📋 Estructura del Proyecto:${NC}"
    echo ""
    echo -e "${YELLOW}Domain Layer:${NC}"
    echo "  └── app/domain/"
    echo "      ├── models/"
    echo "      ├── repositories/"
    echo "      ├── mappers/"
    echo "      └── use-cases/"
    echo ""
    echo -e "${YELLOW}Infrastructure Layer:${NC}"
    echo "  └── app/infrastructure/"
    echo "      ├── dto/"
    echo "      ├── repositories/"
    echo "      └── services/"
    echo ""
    echo -e "${YELLOW}Application Layer:${NC}"
    echo "  └── app/application/"
    echo "      └── use-cases/"
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función para validar estructura
validate_structure() {
    echo -e "${BLUE}✅ Ejecutando validación de estructura...${NC}"
    bash "$(dirname "$0")/commands/validate.sh"
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función para inspeccionar módulo
inspect_module() {
    echo -e "${BLUE}🔍 Ejecutando inspección de módulo...${NC}"
    bash "$(dirname "$0")/commands/inspect.sh"
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función para mostrar ayuda
show_help() {
    bash "$(dirname "$0")/commands/help.sh"
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función para limpiar módulo
clean_module() {
    echo -e "${RED}🧹 Limpieza de Módulo${NC}"
    echo ""
    read -p "Nombre del directorio del módulo a limpiar: " module_name

    if [ -z "$module_name" ]; then
        echo -e "${RED}❌ Error: El nombre del módulo no puede estar vacío${NC}"
        read -p "Presiona Enter para continuar..."
        return
    fi

    echo ""
    echo -e "${YELLOW}⚠️  Esta acción eliminará:${NC}"
    echo "  - src/app/domain/models/${module_name}/"
    echo "  - src/app/domain/repositories/${module_name}/"
    echo "  - src/app/domain/mappers/${module_name}/"
    echo "  - src/app/infrastructure/dto/${module_name}/"
    echo "  - src/app/infrastructure/repositories/${module_name}/"
    echo "  - src/app/infrastructure/services/${module_name}/"
    echo ""

    read -p "¿Estás seguro? (s/n): " confirm

    if [[ $confirm == "s" || $confirm == "S" ]]; then
        rm -rf "src/app/domain/models/${module_name}"
        rm -rf "src/app/domain/repositories/${module_name}"
        rm -rf "src/app/domain/mappers/${module_name}"
        rm -rf "src/app/infrastructure/dto/${module_name}"
        rm -rf "src/app/infrastructure/repositories/${module_name}"
        rm -rf "src/app/infrastructure/services/${module_name}"

        echo -e "${GREEN}✅ Módulo '${module_name}' eliminado exitosamente${NC}"
    else
        echo -e "${YELLOW}⚠️  Operación cancelada${NC}"
    fi

    read -p "Presiona Enter para continuar..."
}

# Loop principal
while true; do
    show_banner
    show_main_menu

    read -p "$(echo -e ${CYAN}Opción: ${NC})" option

    case $option in
        1)
            create_model
            echo ""
            read -p "Presiona Enter para continuar..."
            ;;
        2)
            create_service
            echo ""
            read -p "Presiona Enter para continuar..."
            ;;
        3)
            create_repository
            echo ""
            read -p "Presiona Enter para continuar..."
            ;;
        4)
            create_full_module
            echo ""
            read -p "Presiona Enter para continuar..."
            ;;
        5)
            create_use_case
            echo ""
            read -p "Presiona Enter para continuar..."
            ;;
        6)
            view_structure
            ;;
        7)
            validate_structure
            ;;
        8)
            inspect_module
            ;;
        9)
            clean_module
            ;;
        "?"|"h"|"help")
            show_help
            ;;
        0)
            echo -e "${GREEN}👋 ¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opción inválida${NC}"
            sleep 1
            ;;
    esac
done

