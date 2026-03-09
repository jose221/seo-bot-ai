-- Agregar campos de reporte global a audit_url_validations
-- Reporte global: resumen consolidado de todas las URLs validadas

ALTER TABLE audit_url_validations
    ADD COLUMN IF NOT EXISTS global_report_pdf_path VARCHAR,
    ADD COLUMN IF NOT EXISTS global_report_word_path VARCHAR,
    ADD COLUMN IF NOT EXISTS global_report_ai_text TEXT;

COMMENT ON COLUMN audit_url_validations.global_report_pdf_path IS 'Ruta al PDF del reporte global consolidado';
COMMENT ON COLUMN audit_url_validations.global_report_word_path IS 'Ruta al Word del reporte global consolidado';
COMMENT ON COLUMN audit_url_validations.global_report_ai_text IS 'Texto/respuesta de la IA del reporte global consolidado';

