📘 DOCUMENTO MAESTRO: SEO & AI AGENT BOT
Versión: 1.0 Stack: FastAPI (Python 3.11), SQLModel (Postgres), Playwright, Docker. Objetivo: Desarrollar un sistema de auditoría web inteligente que utiliza una API centralizada externa para Autenticación e Inteligencia Artificial.
Base de datos postgressql = nombre de la base de datos seo_bot_db
1. ARQUITECTURA Y ESTRUCTURA DE ARCHIVOS
   El proyecto debe seguir estrictamente esta estructura de carpetas ("Clean Architecture") para mantener la separación de responsabilidades.

Plaintext
seo-bot-ai/
├── app/
│   ├── main.py              # Inicialización de FastAPI, CORS y Routers.
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (Variables de entorno: DB_URL, EXT_API_URL).
│   │   └── database.py      # Configuración de AsyncEngine con SQLModel.
│   ├── models/              # Tablas de Base de Datos (SQLModel).
│   │   ├── user.py          # Tabla espejo del usuario (Shadow User).
│   │   ├── webpage.py       # Sitios a auditar (Targets).
│   │   └── audit.py         # Resultados de reportes (JSONB).
│   ├── schemas/             # Pydantic Models (Data Transfer Objects).
│   │   ├── auth_schemas.py  # Mapas exactos de I/O de la API externa de Auth.
│   │   ├── ai_schemas.py    # Mapas para la API de IA (Chat Completions).
│   │   └── audit_schemas.py # Schemas para crear/leer reportes.
│   ├── api/
│   │   ├── deps.py          # Middleware de Seguridad (Verify Token & Sync User).
│   │   └── v1/
│   │       ├── api.py       # Router principal que agrupa endpoints.
│   │       └── endpoints/
│   │           ├── auth.py    # Proxy para Login/Register externo.
│   │           ├── targets.py # CRUD de páginas web.
│   │           └── audits.py  # Trigger de auditorías.
│   ├── services/            # Lógica de Negocio y Clientes Externos.
│   │   ├── auth_provider.py # Cliente HTTP para API externa (Auth).
│   │   ├── ai_client.py     # Cliente HTTP para API externa (IA).
│   │   └── audit_engine.py  # Lógica Core: Playwright + Lighthouse Wrapper.
├── tests/                   # Tests unitarios.
├── docker-compose.yml       # Orquestación (App + DB Postgres).
├── Dockerfile               # Imagen Híbrida (Python + Node.js + Chrome).
└── requirements.txt         # Dependencias Python.
2. CONTRATOS DE INTEGRACIÓN (APIS EXTERNAS)
   El bot actúa como cliente. No debe inventar parámetros. Debe usar estrictamente estos contratos.

2.1 API de Autenticación (Identity Provider)

Base URL: https://your-external-api-url.com

A. Endpoint: LOGIN

Método: POST

Ruta: /auth/login

Uso: El Bot recibe credenciales del usuario y las reenvía aquí.

Request Body (JSON):

JSON
{
"email": "user@example.com",
"password": "string",
"project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  // Opcional
"token_name": "SeoBotSession",                         // Opcional
"expires_in_days": 30                                  // Opcional
}
Response Exitosa (200 OK):

JSON
{
"access_token": "eyJhbGciOiJIUz...",
"token_type": "Bearer",
"token_id": "uuid-string",
"user_id": "uuid-string",       // GUARDAR COMO external_id EN BD LOCAL
"user_email": "user@example.com",
"user_name": "Juan Perez",
"tenant_id": "uuid-string",     // GUARDAR EN BD LOCAL
"project_id": "uuid-string",    // GUARDAR EN BD LOCAL
"expires_at": "2025-11-28T21:32:13.947Z",
"scope": "user"
}
B. Endpoint: VERIFY TOKEN

Método: POST

Ruta: /auth/verify-token?token={TOKEN_STRING}

Uso: Middleware del Bot para validar si una petición es lícita.

Body: Vacío.

Response Exitosa (200 OK): Devuelve el mismo JSON que el Login (ver arriba).

Errores Esperados:

401 Unauthorized: Token expirado o inválido. -> Acción Bot: Rechazar petición.

422 Validation Error: Formato incorrecto.

C. Endpoint: REGISTER

Método: POST

Ruta: /auth/register/user

Request Body:

JSON
{
"city": "Mexico City",
"country_code": "MX",
"email": "newuser@test.com",
"full_name": "New User",
"password": "securePass123",
"project_id": "uuid-existing-project",
"username": "newuser"
}
2.2 API de Inteligencia Artificial

Base URL: https://your-external-api-url.com

A. Endpoint: CHAT COMPLETIONS

Método: POST

Ruta: /agent/v1/chat/completions

Request Body (Configuración Estándar para el Bot):

JSON
{
"messages": [
{ "role": "system", "content": "Eres un experto SEO...", "isContext": true },
{ "role": "user", "content": "Analiza este HTML..." }
],
"model": "deepseek-chat",     // O "lowest" para tareas simples
"stream": false,              // False para simplificar manejo en backend
"mcp_tools": [                // Habilitar herramientas si se requiere
{
"server_name": "playwright",
"command": "npx",
"args": ["-y", "@playwright/mcp@latest"]
}
]
}
3. MANEJO DE ERRORES Y RESPUESTAS
   El Bot debe estandarizar sus salidas para el Frontend.

Excepción en API Externa (500/Timeout):

Response: HTTP 503 Service Unavailable

Body: {"detail": "Authentication service is temporarily unavailable."}

Error de Validación (400/422):

Response: HTTP 400 Bad Request

Body: {"detail": "Invalid credentials or parameters."}

Token Inválido (401):

Response: HTTP 401 Unauthorized

Body: {"detail": "Could not validate credentials."}

4. DETALLE DE IMPLEMENTACIÓN (CÓDIGO CLAVE)
   A. Modelo de Datos: User (Sincronización)

Archivo: app/models/user.py

Python
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

class User(SQLModel, table=True):
__tablename__ = "users"
id: UUID = Field(default_factory=uuid4, primary_key=True)
external_id: UUID = Field(unique=True, index=True) # ID de Herandro API
email: str = Field(index=True)
full_name: str
tenant_id: UUID
project_id: Optional[UUID] = Field(default=None, index=True)
last_synced_at: datetime = Field(default_factory=datetime.utcnow)
B. Middleware de Seguridad: get_current_user

Archivo: app/api/deps.py Lógica Crítica:

Extraer token.

Verificar en API Externa.

Si la API Externa dice OK -> Verificar si existe en DB Local.

Si no existe en DB Local -> INSERT (Registrar shadow user).

Si existe -> UPDATE (Sincronizar datos recientes).

Retornar objeto Usuario.

5. TASK LIST (HOJA DE RUTA PASO A PASO)
   Asigna estas tareas al agente desarrollador en este orden exacto.

FASE 1: Infraestructura y Entorno Híbrido

Crear Dockerfile: Debe basarse en python:3.11-slim. Instalar curl, gnupg. Instalar Node.js v20. Instalar lighthouse globalmente (npm i -g lighthouse). Copiar requirements.txt e instalar dependencias Python. Instalar navegadores Playwright (playwright install --with-deps chromium).

Crear docker-compose.yml: Definir servicio db (Postgres 15) y web (FastAPI). Configurar variable de entorno HERANDRO_API_URL.

Dependencias Python: Crear requirements.txt con: fastapi, uvicorn, sqlmodel, asyncpg, httpx, playwright, playwright-lighthouse, python-multipart.

FASE 2: Capa de Autenticación (Proxy & Middleware)

Schemas Auth: Crear app/schemas/auth_schemas.py replicando exactamente los JSONs definidos en la Sección 2.1 de este documento.

Auth Service: Crear app/services/auth_provider.py usando httpx. Implementar métodos login(), register(), verify_token(). Importante: Manejar excepciones httpx.HTTPError y transformarlas en HTTPException de FastAPI.

Modelo User: Implementar app/models/user.py.

Middleware: Implementar app/api/deps.py con la lógica de "Shadow User" (Verificar Externo -> Guardar Local).

Endpoints Auth: Crear app/api/v1/endpoints/auth.py. Exponer /login y /register que actúen como pasarela a la API externa.

FASE 3: Gestión de Targets (Objetivos)

Modelo WebPage: Crear app/models/webpage.py. Campos: id, user_id (FK), url, instructions (Text), tech_stack.

Endpoints CRUD: Crear app/api/v1/endpoints/targets.py. Permitir POST /targets (solo auth users). Validar URL.

FASE 4: Motores de Análisis (IA + Playwright)

Cliente IA: Crear app/services/ai_client.py. Método analyze_content(prompt, context) conectando a /chat/completions. Usar el modelo deepseek-chat.

Motor Lighthouse: Crear app/services/audit_engine.py.

Función run_audit_local(url).

Debe lanzar Playwright -> Conectar Lighthouse -> Extraer JSON -> Filtrar métricas (LCP, SEO Score).

Integración Navegación: Añadir lógica para ejecutar instructions antes de auditar (ej. clicks simples).

FASE 5: Reportes y Orquestación

Modelo AuditReport: Crear tabla en app/models/audit.py con campos JSONB para lighthouse_data y ai_suggestions.

Endpoint Auditoría: Crear POST /audit/{target_id}.

Crucial: Usar BackgroundTasks de FastAPI. No hacer esperar al usuario.

Retornar task_id.

Worker Lógica: El background task debe:

Ejecutar Playwright/Lighthouse.

Enviar HTML a la IA con el prompt: "Analiza estructura para SEO y UX".

Guardar todo en DB.

Instrucción de Inicio: Proceda con la Fase 1. Genere los archivos de configuración (Dockerfile, docker-compose) y la estructura de carpetas vacía. No avance a la Fase 2 hasta que el contenedor levante correctamente.
