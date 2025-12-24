# Base image con Python 3.11
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=20 \
    DISPLAY=:99 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema en una sola capa optimizada
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    xvfb \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./chrome.deb \
    && rm chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación de Chrome
RUN google-chrome --version

# Instalar Node.js v20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

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

# Verificar estructura y agregar el directorio al PYTHONPATH
RUN ls -la /app && \
    if [ -d "/app/app" ]; then echo "✓ Módulo app encontrado"; else echo "✗ ERROR: Módulo app no encontrado"; exit 1; fi

ENV PYTHONPATH=/app

# Exponer puerto
EXPOSE 8000

# Iniciar Xvfb y luego uvicorn (sin --reload en producción)
CMD ["/bin/sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset & sleep 2 && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

