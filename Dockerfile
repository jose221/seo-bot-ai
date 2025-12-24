# Stage 1: Build process
FROM node:20-alpine AS builder

# Check: https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec9ee063c5aaaf153#nodealpine
# Instalar dependencias necesarias para node-gyp u otros módulos nativos si fuera necesario
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Aumentar memoria para evitar OOM (Out of Memory) en servidores pequeños
ENV NODE_OPTIONS="--max-old-space-size=4096"

COPY package*.json ./

# Instalar dependencias con legacy-peer-deps para compatibilidad
RUN npm install --legacy-peer-deps

COPY . .

# Ejecutar el build.
# Nota: Asegúrate de que 'npm run build' ejecute 'ng build --configuration production'
RUN npm run build

# Lógica de verificación simplificada directamente al destino final
RUN mkdir -p /app/final-dist && \
    if [ -d "dist/seo-bot-ai/browser" ]; then \
        cp -r dist/seo-bot-ai/browser/* /app/final-dist/; \
    elif [ -d "dist/seo-bot-ai" ]; then \
        cp -r dist/seo-bot-ai/* /app/final-dist/; \
    else \
        cp -r dist/* /app/final-dist/; \
    fi

# Stage 2: Production server
FROM nginx:stable-alpine

# Limpiar el directorio por defecto de nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar configuración completa de nginx (reemplaza el nginx.conf principal)
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar desde la carpeta normalizada en la etapa anterior
COPY --from=builder /app/final-dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
