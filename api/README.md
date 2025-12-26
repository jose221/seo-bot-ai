# SEO Bot AI - API Backend

Sistema de auditoría web inteligente con análisis SEO automatizado e integración con IA.

## Características principales

- **Autenticación delegada**: Integración con API externa
- **Shadow User Pattern**: Sincronización automática de usuarios sin almacenar contraseñas
- **Auditorías SEO**: Análisis técnico mediante Playwright y Lighthouse
- **IA integrada**: Análisis inteligente con modelos de lenguaje
- **Arquitectura híbrida**: Python + Node.js con soporte Docker

## Stack tecnológico

- **Framework**: FastAPI + Python 3.11+
- **Base de datos**: PostgreSQL 15 + SQLModel
- **Testing web**: Playwright + Chromium
- **Inteligencia artificial**: Integración con servicios de IA externos
- **Containerización**: Docker + Docker Compose

## Instalación

### Requisitos previos

- Python 3.11 o superior
- PostgreSQL 15
- Docker y Docker Compose (opcional pero recomendado)

### Configuración local

**1. Clonar repositorio y crear entorno virtual**

```bash
git clone https://github.com/your-username/seo-bot-ai.git
cd seo-bot-ai/api
python3 -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate
```

**2. Instalar dependencias**

```bash
pip install -r requirements.txt
playwright install chromium
```

**3. Configurar variables de entorno**

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/seo_bot_db
HERANDRO_API_URL=https://your-external-api-url.com
SECRET_KEY=your-secret-key-here
DEBUG=True
```

> **Nota de seguridad**: Los archivos `.env` y configuraciones de producción están excluidos del control de versiones mediante `.gitignore`. Solo se versiona `.env.example` como plantilla.

**4. Configurar base de datos**

```bash
# Crear base de datos
createdb seo_bot_db

# Ejecutar migraciones
./sql.sh up
```

**5. Iniciar servidor de desarrollo**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- Documentación Swagger: http://localhost:8000/docs
- Documentación ReDoc: http://localhost:8000/redoc

### Configuración con Docker

**1. Levantar servicios**

```bash
docker-compose up -d
```

**2. Verificar logs**

```bash
docker-compose logs -f web
```

**3. Detener servicios**

```bash
docker-compose down
```

## Uso de la API

### Autenticación

**Registro de usuario**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "Juan Perez",
    "username": "juanp",
    "city": "Mexico City",
    "country_code": "MX"
  }'
```

**Login**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Respuesta exitosa:
```json
{
  "access_token": "eyJhbGciOiJIUz...",
  "token_type": "Bearer",
  "user_id": "uuid-here",
  "expires_at": "2025-12-28T21:32:13.947Z"
}
```

**Acceder a endpoints protegidos**

```bash
curl -X GET "http://localhost:8000/api/v1/protected-endpoint" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Arquitectura del proyecto

```
api/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py        # Configuración con Pydantic Settings
│   │   └── database.py      # SQLModel + AsyncEngine
│   ├── models/              # Modelos de base de datos (SQLModel)
│   │   └── user.py          # Shadow User model
│   ├── schemas/             # DTOs con Pydantic
│   │   └── auth_schemas.py  # Contratos de autenticación
│   ├── api/
│   │   ├── deps.py          # Middleware y dependencias
│   │   └── v1/
│   │       └── endpoints/   # Endpoints REST organizados
│   └── services/
│       └── auth_provider.py # Cliente HTTP para API externa
├── bd/
│   ├── tables.sql           # Schema de base de datos
│   └── seeder.sql           # Datos de prueba
├── sql.sh                   # Script de gestión de BD
├── requirements.txt         # Dependencias Python
├── .env.example            # Plantilla de configuración
└── Dockerfile              # Imagen Docker
```

## Seguridad

### Shadow User Pattern

El sistema implementa el patrón Shadow User para máxima seguridad:

1. La autenticación se delega a una API externa
2. Cada petición valida el token contra el servicio externo
3. Los datos del usuario se sincronizan automáticamente en la BD local
4. No se almacenan contraseñas en la base de datos local
5. El token externo es la única fuente de verdad para autenticación

### Protección de información sensible

- Los archivos de configuración (`*.env`, `environment.ts`, `environment.prod.ts`) están excluidos del repositorio
- Se proporciona `.env.example` como plantilla sin datos sensibles
- Las credenciales de producción deben configurarse mediante variables de entorno

## Testing

```bash
# Ejecutar suite completa
pytest

# Con reporte de cobertura
pytest --cov=app tests/

# Modo verbose
pytest -v
```

## Variables de entorno

| Variable | Descripción | Requerido | Ejemplo |
|----------|-------------|-----------|---------|
| `DATABASE_URL` | URL de conexión PostgreSQL | Sí | `postgresql+asyncpg://user:pass@localhost/seo_bot_db` |
| `HERANDRO_API_URL` | URL de API externa | Sí | `https://your-external-api-url.com` |
| `SECRET_KEY` | Clave secreta para JWT | Sí (producción) | `tu-clave-secreta-segura` |
| `DEBUG` | Modo debug | No | `False` |
| `DB_HOST` | Host de PostgreSQL | Sí (producción) | `localhost` |
| `DB_PORT` | Puerto de PostgreSQL | Sí (producción) | `5432` |
| `DB_USER` | Usuario de base de datos | Sí (producción) | `your_db_user` |
| `DB_PASSWORD` | Contraseña de base de datos | Sí (producción) | `***` |
| `DB_NAME` | Nombre de base de datos | Sí (producción) | `seo_bot_db` |

## Script de gestión de base de datos

El archivo `sql.sh` proporciona comandos para gestionar la base de datos:

```bash
# Modo local (localhost)
./sql.sh

# Modo producción (carga config desde .env)
./sql.sh --prod
```

Opciones disponibles:
1. Crear/actualizar estructura (tables.sql)
2. Sembrar datos de desarrollo (seeder.sql)
3. Reset completo (drop + up + seed)
4. Backup a bd/migration.sql
5. Restore desde bd/migration.sql

## Roadmap de desarrollo

- [x] Fase 1: Infraestructura base y containerización
- [x] Fase 2: Sistema de autenticación y Shadow User
- [ ] Fase 3: Gestión de targets (URLs a auditar)
- [ ] Fase 4: Motor de auditorías (Playwright + Lighthouse)
- [ ] Fase 5: Integración completa con IA para análisis SEO

## Troubleshooting

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL esté ejecutándose
pg_isready

# Probar conexión directa
psql -U postgres -d seo_bot_db

# Verificar logs de Docker
docker-compose logs postgres
```

### Playwright no encuentra navegador

```bash
# Reinstalar navegadores de Playwright
playwright install chromium

# Verificar instalación
playwright install --dry-run
```

### Puerto 8000 en uso

```bash
# Cambiar puerto en comando
uvicorn app.main:app --reload --port 8001

# O configurar variable de entorno
export PORT=8001
uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
```

### Problemas con dependencias

```bash
# Limpiar cache de pip
pip cache purge

# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

## Documentación adicional

- [Instrucciones maestras del proyecto](instructions.md)
- [Guía de desarrollo](../DEV-GUIDE.md)
- API interactiva: `/docs` (Swagger UI)
- Documentación alternativa: `/redoc`

## Contribución

Este proyecto sigue un flujo de trabajo basado en feature branches. Para contribuir:

1. Crea una rama desde `main`
2. Implementa los cambios
3. Ejecuta los tests
4. Crea un pull request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo [LICENSE](../LICENSE) para más detalles.

