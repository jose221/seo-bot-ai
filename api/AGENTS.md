# AGENTS.md

## Big Picture (FastAPI + async API + background jobs)
- Entrada real: `app/main.py` (no usar `main.py` raíz; es un hello-world aislado).
- API v1 en `app/api/v1/api.py` con routers `auth`, `targets`, `audits`, `downloads`, `sitemaps` bajo `/api/v1`.
- Seguridad: JWT Keycloak + UMA en `app/core/security.py`; sincronización Shadow User en `app/api/deps.py#get_current_user`.
- Persistencia híbrida en `app/core/database.py`: endpoints usan `AsyncSession`; tareas pesadas usan `db_manager.sync_session_context()`.
- Flujo principal: Target (`web_pages`) -> Audit (`audit_reports`) -> Comparison/Schema/URL validation -> reportes en `storage/reports`.

## Service Boundaries y Data Flow
- Endpoints orquestan; lógica pesada vive en `app/services/*` (ej. `audit_engine.py`, `schema_audit_service.py`, `url_validation_service.py`).
- `POST /audits` dispara `BackgroundTasks` y cambia estados `pending -> in_progress -> completed|failed` (`AuditStatus`, `ComparisonStatus`, etc.).
- Ojo: hay dos `run_audit_task`; el endpoint usa el definido en `app/api/v1/endpoints/audits.py`, no el de `app/services/background_tasks.py`.
- Los campos JSON grandes (`lighthouse_data`, `ai_suggestions`, `results_json`) se excluyen en listados para performance (`audits.py` usa selects ligeros y SQL crudo en URL validations).
- Reportes (PDF/Excel/Word) se regeneran on-demand si faltan en `get_audit` y `list_audits`.

## Integraciones Externas
- Keycloak: JWKS + issuer validation + UMA decision endpoint (`resource_guard(...)` en `app/core/security.py`).
- Herandro Auth proxy: `app/services/auth_provider.py` (`/auth/login`, `/auth/register/user`, `/auth/verify-token`).
- Herandro AI: `app/services/ai_client.py` hacia `/agent/v1/chat/completions` con prompts Jinja en `app/prompts/*.jinja`.
- Cliente HSA server-to-server: `app/shared/herandro_services_api/herandro_services_api_client.py` toma token desde `ContextVar` del request.
- Cache externa HTTP en `app/services/cache.py` (usa `HERANDRO_API_URL`), además de caché local de sitemaps en `storage/sitemaps/*.json`.

## Convenciones de Implementación (específicas del repo)
- Enums string para estado en modelos (`pending|in_progress|completed|failed`) y casts `sql_cast(..., String)` en queries.
- Multi-tenant por usuario: casi todas las consultas filtran `model.user_id == current_user.id`.
- Para URL batches, parseo tolerante en `UrlValidationService.parse_urls` (split por `\n`, coma o espacio + dedupe).
- SEO/auditoría anti-bot: `AuditEngine` intenta Playwright stealth y cae a `nodriver` si detecta DataDome.
- Fallback de scraping: `targets.py#get_target_html` usa live scrape y, si falla, `manual_html_content` almacenado.
- Patrones singleton/factory frecuentes: `get_audit_engine()`, `get_ai_client()`, `get_schema_audit_service()`, `get_url_validation_service()`.

## Workflows de Desarrollo
- Setup local mínimo: `python3 -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt && playwright install chromium`.
- Ejecutar API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- Smoke test rápido sin DB completa: `python test_structure.py`.
- Script útil para BD: `./sql.sh` (menú interactivo) o `./sql.sh --prod` para cargar credenciales de `.env`.
- Docker runtime relevante: `Dockerfile` instala Chrome + Node 20 + Lighthouse + Xvfb para scraping headless/híbrido.

## Archivos de Referencia Rápida
- Config y arranque: `app/main.py`, `app/core/config.py`, `app/core/database.py`.
- API y seguridad: `app/api/deps.py`, `app/core/security.py`, `app/api/v1/endpoints/audits.py`.
- Dominio/modelos: `app/models/audit.py`, `app/models/audit_comparison.py`, `app/models/audit_url_validation.py`, `app/models/webpage.py`.
- Integraciones IA/Auth: `app/services/ai_client.py`, `app/services/auth_provider.py`, `app/shared/herandro_services_api/herandro_services_api_client.py`.
- Reportes y caché: `app/services/report_generator.py`, `app/services/cache.py`, `app/services/sitemap_cache.py`.

