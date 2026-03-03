-- Migración: Agregar columnas tags y provider a web_pages
-- Fecha: 2026-03-02

-- tags: array de strings para agrupar targets (ej. ['hotel list', 'landing pages'])
ALTER TABLE web_pages
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT NULL;

-- provider: proveedor o empresa asociada (ej. 'Pricetravel', 'Facebook')
ALTER TABLE web_pages
    ADD COLUMN IF NOT EXISTS provider VARCHAR(200) DEFAULT NULL;

-- Índice GIN para búsquedas eficientes dentro del array tags
CREATE INDEX IF NOT EXISTS idx_web_pages_tags ON web_pages USING GIN (tags);

-- Índice B-tree para filtrar por provider
CREATE INDEX IF NOT EXISTS idx_web_pages_provider ON web_pages (provider);

UPDATE tabla
SET tags = ARRAY['Hotel list']
WHERE id = 123;
