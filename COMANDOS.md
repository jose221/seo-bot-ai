# 🚀 Comandos Rápidos - SEO Bot AI

## 📦 Instalación y Setup

```bash
# Crear entorno virtual
python3 -m venv myenv

# Activar entorno
source myenv/bin/activate  # Linux/Mac
# o
myenv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores Playwright
playwright install chromium

# Crear archivo .env
cp .env.example .env
```

## 🐳 Docker

```bash
# Iniciar todos los servicios
docker-compose up -d

# Iniciar solo la base de datos
docker-compose up -d db

# Ver logs en tiempo real
docker-compose logs -f web

# Detener servicios
docker-compose down

# Reconstruir imágenes
docker-compose build --no-cache

# Ver estado de servicios
docker-compose ps

# Acceder al contenedor
docker-compose exec web bash

# Resetear todo (¡cuidado!)
docker-compose down -v
```

## 🚀 Desarrollo Local

```bash
# Activar entorno virtual
source myenv/bin/activate

# Iniciar servidor con hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Iniciar en otro puerto
uvicorn app.main:app --reload --port 8001

# Ver logs en modo debug
DEBUG=True uvicorn app.main:app --reload
```

## 🧪 Testing

```bash
# Ejecutar test de estructura
python test_structure.py

# Ejecutar todos los tests (cuando estén implementados)
pytest

# Tests con coverage
pytest --cov=app tests/

# Tests con verbose
pytest -v

# Tests específicos
pytest tests/test_auth.py
```

## 🔍 Debugging

```bash
# Ver estructura del proyecto
./show_structure.sh

# Verificar instalación de dependencias
pip list | grep -E 'fastapi|uvicorn|sqlmodel|httpx|playwright'

# Verificar variables de entorno
cat .env

# Verificar conexión a PostgreSQL
psql -U postgres -d seo_bot_db -h localhost

# Ver logs de la aplicación
tail -f logs/app.log  # Si está configurado
```

## 🌐 API Testing

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Login (cambiar credenciales)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new@example.com",
    "password": "SecurePass123",
    "full_name": "New User",
    "username": "newuser",
    "city": "Mexico City",
    "country_code": "MX"
  }'

# Endpoint protegido (cambiar TOKEN)
curl -X GET "http://localhost:8000/api/v1/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📊 Base de Datos

```bash
# Conectar a PostgreSQL (local)
psql -U postgres -d seo_bot_db

# Conectar a PostgreSQL (Docker)
docker-compose exec db psql -U postgres -d seo_bot_db

# Ver tablas
\dt

# Describir tabla users
\d users

# Ver usuarios
SELECT * FROM users;

# Resetear base de datos
DROP DATABASE seo_bot_db;
CREATE DATABASE seo_bot_db;

# Backup
pg_dump -U postgres seo_bot_db > backup.sql

# Restore
psql -U postgres seo_bot_db < backup.sql
```

## 🔄 Git

```bash
# Estado
git status

# Agregar cambios
git add .

# Commit
git commit -m "feat: implementación de fases 1 y 2"

# Push
git push origin main

# Ver logs
git log --oneline --graph

# Crear rama
git checkout -b feature/fase-3
```

## 📦 Gestión de Dependencias

```bash
# Listar dependencias instaladas
pip list

# Ver dependencias desactualizadas
pip list --outdated

# Instalar nueva dependencia
pip install nombre-paquete

# Actualizar requirements.txt
pip freeze > requirements.txt

# Actualizar una dependencia específica
pip install --upgrade nombre-paquete
```

## 🛠️ Mantenimiento

```bash
# Limpiar cache de Python
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Limpiar cache de Playwright
playwright cache clean

# Ver espacio usado por Docker
docker system df

# Limpiar Docker
docker system prune -a

# Actualizar pip
pip install --upgrade pip
```

## 📖 Documentación

```bash
# Abrir Swagger UI
open http://localhost:8000/docs

# Abrir ReDoc
open http://localhost:8000/redoc

# Generar OpenAPI JSON
curl http://localhost:8000/openapi.json > openapi.json
```

## 🔐 Seguridad

```bash
# Generar SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Ver tokens JWT (instalar jwt-cli)
jwt decode YOUR_TOKEN

# Verificar variables de entorno sensibles
grep -i "secret\|password" .env
```

## 📱 Productividad

```bash
# Alias útiles (agregar a ~/.zshrc o ~/.bashrc)
alias seobot-start="cd ~/seo-bot-ai && docker-compose up -d"
alias seobot-stop="cd ~/seo-bot-ai && docker-compose down"
alias seobot-logs="cd ~/seo-bot-ai && docker-compose logs -f"
alias seobot-shell="cd ~/seo-bot-ai && docker-compose exec web bash"
alias seobot-db="cd ~/seo-bot-ai && docker-compose exec db psql -U postgres -d seo_bot_db"

# Recargar configuración
source ~/.zshrc  # o ~/.bashrc
```

## 🎯 Comandos por Fase

### Fase 1-2 (Actual)
```bash
# Verificar estructura
python test_structure.py

# Iniciar servicios
docker-compose up -d

# Ver documentación
open http://localhost:8000/docs
```

### Fase 3 (Próxima)
```bash
# Crear modelo WebPage
touch app/models/webpage.py

# Crear endpoints targets
touch app/api/v1/endpoints/targets.py

# Tests
pytest tests/test_targets.py
```

### Fase 4 (Futura)
```bash
# Crear audit engine
touch app/services/audit_engine.py

# Crear AI client
touch app/services/ai_client.py

# Tests de integración
pytest tests/integration/test_audit.py
```

---

## 🆘 Troubleshooting

```bash
# Error: Puerto 8000 ocupado
lsof -ti:8000 | xargs kill -9

# Error: PostgreSQL no inicia
docker-compose restart db
docker-compose logs db

# Error: Playwright no encuentra navegador
playwright install --force chromium

# Error: Import no funciona
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Error: Permisos
chmod +x show_structure.sh
chmod +x *.sh
```

---

## 📌 Enlaces Útiles

- Documentación FastAPI: https://fastapi.tiangolo.com
- Documentación Playwright: https://playwright.dev/python
- Documentación SQLModel: https://sqlmodel.tiangolo.com
- Documentación Pydantic: https://docs.pydantic.dev

---

**Última actualización:** 28 de Noviembre, 2025

