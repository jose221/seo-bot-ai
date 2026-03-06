-- ============================================
-- DIAGNÓSTICO DE RENDIMIENTO - TARGETS / WEB_PAGES
-- Ejecutar en la base de datos para identificar cuellos de botella
-- ============================================

-- 1. Ver índices existentes en web_pages
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'web_pages'
ORDER BY indexname;

-- 2. Ver índices existentes en audit_reports
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'audit_reports'
ORDER BY indexname;

-- 3. Tamaño de las tablas (datos + índices)
SELECT
    relname AS tabla,
    pg_size_pretty(pg_total_relation_size(relid)) AS tamaño_total,
    pg_size_pretty(pg_relation_size(relid)) AS tamaño_datos,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS tamaño_indices,
    n_live_tup AS filas_vivas,
    n_dead_tup AS filas_muertas
FROM pg_stat_user_tables
WHERE relname IN ('web_pages', 'audit_reports', 'audit_comparisons', 'audit_schema_reviews', 'audit_url_validations', 'users')
ORDER BY pg_total_relation_size(relid) DESC;

-- 4. EXPLAIN ANALYZE de la query list_targets (la más problemática)
-- Simula: GET /targets con joinedload(audit_reports)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT web_pages.*, audit_reports.*
FROM web_pages
LEFT OUTER JOIN audit_reports ON web_pages.id = audit_reports.web_page_id
WHERE web_pages.user_id = (SELECT id FROM users LIMIT 1)
  AND web_pages.is_active = true
ORDER BY web_pages.created_at DESC;

-- 5. EXPLAIN ANALYZE del conteo (otra query problemática)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM web_pages
WHERE user_id = (SELECT id FROM users LIMIT 1)
  AND is_active = true;

-- 6. Verificar si hay columnas JSONB/TEXT pesadas en audit_reports
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'audit_reports'
ORDER BY ordinal_position;

-- 7. Tamaño promedio de las columnas JSONB en audit_reports
SELECT
    AVG(pg_column_size(lighthouse_data)) AS avg_lighthouse_bytes,
    AVG(pg_column_size(ai_suggestions)) AS avg_ai_suggestions_bytes,
    AVG(pg_column_size(seo_analysis)) AS avg_seo_analysis_bytes,
    MAX(pg_column_size(lighthouse_data)) AS max_lighthouse_bytes,
    MAX(pg_column_size(ai_suggestions)) AS max_ai_suggestions_bytes,
    MAX(pg_column_size(seo_analysis)) AS max_seo_analysis_bytes
FROM audit_reports;

-- 8. Verificar si falta el índice compuesto en web_pages
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'web_pages'
  AND indexdef LIKE '%is_active%';

-- 9. Verificar índices en audit_reports para web_page_id
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'audit_reports'
  AND indexdef LIKE '%web_page_id%';

-- 10. Verificar si hay índice en audit_reports.status
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'audit_reports'
  AND indexdef LIKE '%status%';

-- 11. Tamaño de la columna manual_html_content en web_pages
SELECT
    COUNT(*) AS total_web_pages,
    COUNT(manual_html_content) AS con_html_manual,
    AVG(LENGTH(manual_html_content)) AS avg_html_length,
    MAX(LENGTH(manual_html_content)) AS max_html_length,
    pg_size_pretty(SUM(pg_column_size(manual_html_content))) AS total_html_size
FROM web_pages
WHERE manual_html_content IS NOT NULL;

-- 12. Verificar si las estadísticas están actualizadas
SELECT
    relname,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN ('web_pages', 'audit_reports');

