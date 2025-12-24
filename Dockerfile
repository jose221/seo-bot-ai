# Etapa 1: Build de la aplicación Angular
FROM node:20-alpine AS builder

WORKDIR /app

# Aumentar memoria de Node.js para el build
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps --force

# Copiar archivos de configuración de Angular
COPY angular.json tsconfig*.json ./

# Copiar el resto de los archivos del proyecto
COPY src ./src
COPY public ./public

# Build de la aplicación para producción (sin SSR por ahora para simplificar)
RUN npm run build -- --configuration production --output-path=dist/browser

# Etapa 2: Servidor de producción con Nginx
FROM nginx:alpine

# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar los archivos build desde la etapa anterior
COPY --from=builder /app/dist/browser /usr/share/nginx/html

# Exponer el puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Comando para iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]

