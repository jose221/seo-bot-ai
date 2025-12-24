# Base image con Python 3.11
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=20 \
    DISPLAY=:99

# Instalar dependencias del sistema + Xvfb (Virtual Display)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome Oficial (mejor evasión que Chromium)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Verificar instalación de Chrome
RUN google-chrome --version

# Instalar Node.js v20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Instalar Lighthouse globalmente
RUN npm install -g lighthouse@12.2.1

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instalar navegadores Playwright
RUN playwright install --with-deps chromium

# Copiar código de la aplicación
COPY . .

# Dar permisos de ejecución al entrypoint
RUN chmod +x ./docker-entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Usar entrypoint para iniciar Xvfb primero
ENTRYPOINT ["./docker-entrypoint.sh"]

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

