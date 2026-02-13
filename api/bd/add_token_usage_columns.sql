-- Agregar columnas de uso de tokens a tabla audit_reports
ALTER TABLE audit_reports ADD COLUMN IF NOT EXISTS input_tokens INT DEFAULT 0;
ALTER TABLE audit_reports ADD COLUMN IF NOT EXISTS output_tokens INT DEFAULT 0;

-- Agregar columnas de uso de tokens a tabla audit_comparisons
ALTER TABLE audit_comparisons ADD COLUMN IF NOT EXISTS input_tokens INT DEFAULT 0;
ALTER TABLE audit_comparisons ADD COLUMN IF NOT EXISTS output_tokens INT DEFAULT 0;

