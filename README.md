# SEO Bot AI 🤖

Sistema de auditoría web inteligente con IA integrada.

## 📋 Características

- ✅ **Autenticación Delegada**: Integración con API externa (Herandro Services)
- 🔐 **Shadow User Pattern**: Sincronización automática de usuarios
- 🎯 **Auditorías SEO**: Análisis con Playwright + Lighthouse
- 🤖 **IA Integrada**: Análisis inteligente con DeepSeek
- 🐳 **Docker Ready**: Entorno híbrido Python + Node.js

## 🛠️ Stack Tecnológico

- **Backend**: FastAPI + Python 3.11+
- **Base de Datos**: PostgreSQL 15 + SQLModel
- **Testing**: Playwright + Chromium
- **IA**: Herandro AI Services (DeepSeek)
- **Containerización**: Docker + Docker Compose

## 🚀 Inicio Rápido

### Pre-requisitos

- Python 3.11+
- PostgreSQL 15
- Docker y Docker Compose (opcional)

### Instalación Local

1. **Clonar el repositorio y crear entorno virtual**:
```bash
python3 -m venv myenv
source myenv/bin/activate  # En Windows: myenv\Scripts\activate
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. **Iniciar PostgreSQL** (si no usas Docker):
```bash
# Crear la base de datos
createdb seo_bot_db
```

5. **Iniciar la aplicación**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Acceder a la documentación**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Instalación con Docker

1. **Levantar los servicios**:
```bash
docker-compose up -d
```

2. **Ver logs**:
```bash
docker-compose logs -f web
```

3. **Detener servicios**:
```bash
docker-compose down
```

## 📚 Uso de la API

### 1. Registro de Usuario

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

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUz...",
  "token_type": "Bearer",
  "user_id": "...",
  "expires_at": "2025-12-28T21:32:13.947Z"
}
```

### 3. Usar Endpoints Protegidos

```bash
curl -X GET "http://localhost:8000/api/v1/some-protected-endpoint" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🏗️ Arquitectura

```
app/
├── main.py              # Punto de entrada FastAPI
├── core/
│   ├── config.py        # Configuración (Pydantic Settings)
│   └── database.py      # SQLModel + AsyncEngine
├── models/              # Modelos de BD (SQLModel)
│   └── user.py          # Shadow User
├── schemas/             # DTOs (Pydantic)
│   └── auth_schemas.py  # Contratos de Auth
├── api/
│   ├── deps.py          # Middleware de seguridad
│   └── v1/
│       └── endpoints/   # Endpoints REST
└── services/
    └── auth_provider.py # Cliente HTTP a API externa
```

## 🔒 Seguridad

El sistema implementa el patrón **Shadow User**:

1. El usuario se autentica en la API externa (Herandro Services)
2. El token es verificado en cada petición
3. Los datos del usuario se sincronizan automáticamente en la BD local
4. No se almacenan contraseñas localmente

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/
```

## 📝 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de conexión PostgreSQL | `postgresql+asyncpg://user:pass@localhost/db` |
| `HERANDRO_API_URL` | URL de API externa | `https://herandro-services-api.herandro.com.mx` |
| `SECRET_KEY` | Clave secreta (producción) | `your-secret-key` |
| `DEBUG` | Modo debug | `False` |

## 📖 Documentación Adicional

- [Instrucciones Maestras](instructions.md)
- API Docs: `/docs` (Swagger)
- API Docs: `/redoc` (ReDoc)

## 🚧 Roadmap

- [x] Fase 1: Infraestructura y Docker
- [x] Fase 2: Autenticación y Shadow User
- [ ] Fase 3: Gestión de Targets (URLs)
- [ ] Fase 4: Motor de Auditorías (Playwright + Lighthouse)
- [ ] Fase 5: Integración con IA (Análisis SEO)

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👨‍💻 Desarrollo

```bash
# Activar entorno virtual
source myenv/bin/activate

# Instalar en modo desarrollo
pip install -r requirements.txt

# Ejecutar con hot-reload
uvicorn app.main:app --reload
```

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
pg_isready

# Verificar conexión
psql -U postgres -d seo_bot_db
```

### Playwright no encuentra el navegador
```bash
# Reinstalar navegadores
playwright install chromium
```

### Puerto 8000 ya está en uso
```bash
# Cambiar el puerto en el comando
uvicorn app.main:app --reload --port 8001
```

