#!/bin/bash
# Script de comandos útiles para Docker

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 SEO Bot AI - Docker Commands${NC}\n"

# Build de la imagen
build() {
    echo -e "${GREEN}📦 Building Docker image...${NC}"
    docker build -t seo-bot-ai:latest .
}

# Ejecutar contenedor en modo desarrollo
dev() {
    echo -e "${GREEN}🚀 Starting development container...${NC}"
    docker run -it --rm \
        -p 8000:8000 \
        -v $(pwd)/app:/app/app \
        -v $(pwd)/.env:/app/.env \
        --name seo-bot-dev \
        seo-bot-ai:latest
}

# Ejecutar con docker-compose
compose-up() {
    echo -e "${GREEN}🚀 Starting with docker-compose...${NC}"
    docker-compose up -d
}

# Ver logs
logs() {
    echo -e "${GREEN}📋 Showing logs...${NC}"
    docker-compose logs -f
}

# Parar contenedores
stop() {
    echo -e "${YELLOW}⏸️  Stopping containers...${NC}"
    docker-compose down
}

# Entrar al contenedor
shell() {
    echo -e "${GREEN}🐚 Opening shell in container...${NC}"
    docker exec -it seo-bot-dev /bin/bash
}

# Limpiar imágenes viejas
clean() {
    echo -e "${YELLOW}🧹 Cleaning old images...${NC}"
    docker system prune -f
}

# Rebuild completo
rebuild() {
    echo -e "${GREEN}♻️  Rebuilding from scratch...${NC}"
    docker-compose down
    docker build --no-cache -t seo-bot-ai:latest .
    docker-compose up -d
}

# Menú de ayuda
help() {
    echo "Available commands:"
    echo "  build       - Build Docker image"
    echo "  dev         - Run in development mode"
    echo "  compose-up  - Start with docker-compose"
    echo "  logs        - View logs"
    echo "  stop        - Stop containers"
    echo "  shell       - Open shell in container"
    echo "  clean       - Clean old images"
    echo "  rebuild     - Rebuild from scratch"
    echo ""
    echo "Usage: ./docker-commands.sh [command]"
}

# Ejecutar comando
case "$1" in
    build)
        build
        ;;
    dev)
        dev
        ;;
    compose-up)
        compose-up
        ;;
    logs)
        logs
        ;;
    stop)
        stop
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    rebuild)
        rebuild
        ;;
    *)
        help
        ;;
esac

