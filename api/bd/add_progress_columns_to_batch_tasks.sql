-- Agregar progreso persistido a tareas batch / masivas

ALTER TABLE audit_url_validations
    ADD COLUMN IF NOT EXISTS progress_percentage INTEGER NOT NULL DEFAULT 0;

ALTER TABLE audit_comparisons
    ADD COLUMN IF NOT EXISTS progress_percentage INTEGER NOT NULL DEFAULT 0;

ALTER TABLE rich_results_reports
    ADD COLUMN IF NOT EXISTS progress_percentage INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN audit_url_validations.progress_percentage IS 'Porcentaje de avance de la validación batch de URLs (0-100)';
COMMENT ON COLUMN audit_comparisons.progress_percentage IS 'Porcentaje de avance de la comparación masiva de auditorías (0-100)';
COMMENT ON COLUMN rich_results_reports.progress_percentage IS 'Porcentaje de avance del reporte Rich Results (0-100)';
