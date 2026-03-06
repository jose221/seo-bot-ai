-- ============================================
-- ÍNDICES PARA OPTIMIZAR RENDIMIENTO DE TARGETS
-- Ejecutar en la base de datos PostgreSQL
-- ============================================

-- 1. Índice compuesto en web_pages (user_id, is_active, created_at DESC)
-- Optimiza: GET /targets (list_targets) y GET /targets/search
-- Antes: Seq Scan en web_pages filtrando por user_id + is_active + ORDER BY created_at
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_web_pages_user_active_created
ON web_pages (user_id, is_active, created_at DESC);

-- 2. Índice en web_pages.is_active
-- Optimiza: Filtros frecuentes por is_active
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_web_pages_is_active
ON web_pages (is_active);

-- 3. Índice en audit_reports.status
-- Optimiza: Filtro only_page_with_audits_completed en search_targets
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_reports_status
ON audit_reports (status);

-- 4. Índice compuesto en audit_reports (web_page_id, status)
-- Optimiza: JOIN entre web_pages y audit_reports con filtro por status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_reports_web_page_status
ON audit_reports (web_page_id, status);

-- 5. Índice en web_pages.provider (se usa en filtros)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_web_pages_provider
ON web_pages (provider) WHERE provider IS NOT NULL;

-- 6. Índice GIN para tags (array) si no existe
-- Optimiza: Filtro por tag con ANY()
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_web_pages_tags_gin
ON web_pages USING GIN (tags);

-- 7. Actualizar estadísticas para que el query planner tome buenas decisiones
ANALYZE web_pages;
ANALYZE audit_reports;
ANALYZE users;

