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
RUN npm run build -- --configuration=production 2>&1 || npm run build 2>&1

# Etapa 2: Servidor de producción con Nginx
FROM nginx:alpine

# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar los archivos build desde la etapa anterior
# Angular 21 genera los archivos en dist/seo-bot-ai/browser
COPY --from=builder /app/dist/seo-bot-ai/browser /usr/share/nginx/html

# Exponer el puerto 80
EXPOSE 80

# Comando para iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]



