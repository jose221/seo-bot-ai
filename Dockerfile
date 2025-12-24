# Etapa 1: Build de la aplicación Angular
FROM node:20-alpine AS builder

WORKDIR /app

# Aumentar memoria de Node.js para el build
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps

# Copiar todos los archivos necesarios para el build
COPY . .

# Build de la aplicación para producción
RUN npm run build

# Verificar y preparar los archivos para nginx
RUN echo "=== Verificando estructura del build ===" && \
    ls -la dist/ && \
    if [ -d "dist/seo-bot-ai/browser" ]; then \
      echo "✓ Encontrado: dist/seo-bot-ai/browser"; \
      mkdir -p /tmp/dist && cp -r dist/seo-bot-ai/browser/* /tmp/dist/; \
    elif [ -d "dist/browser" ]; then \
      echo "✓ Encontrado: dist/browser"; \
      mkdir -p /tmp/dist && cp -r dist/browser/* /tmp/dist/; \
    elif [ -d "dist/seo-bot-ai" ]; then \
      echo "✓ Encontrado: dist/seo-bot-ai"; \
      mkdir -p /tmp/dist && cp -r dist/seo-bot-ai/* /tmp/dist/; \
    elif [ -d "dist" ]; then \
      echo "✓ Usando: dist"; \
      mkdir -p /tmp/dist && cp -r dist/* /tmp/dist/; \
    else \
      echo "✗ ERROR: No se encontró ningún directorio de build!"; \
      exit 1; \
    fi && \
    echo "=== Contenido final ===" && \
    ls -la /tmp/dist/

# Etapa 2: Servidor de producción con Nginx
FROM nginx:alpine

# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar los archivos build desde la etapa anterior
COPY --from=builder /tmp/dist /usr/share/nginx/html

# Exponer el puerto 80
EXPOSE 80

# Comando para iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]



