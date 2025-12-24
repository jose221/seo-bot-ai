-- Migración: Agregar campos de rutas de reportes PDF y Excel
-- Fecha: 2025-12-24

-- Agregar campos a la tabla audit_reports
ALTER TABLE audit_reports
ADD COLUMN IF NOT EXISTS report_pdf_path VARCHAR,
ADD COLUMN IF NOT EXISTS report_excel_path VARCHAR;

-- Agregar campos a la tabla audit_comparisons
ALTER TABLE audit_comparisons
ADD COLUMN IF NOT EXISTS report_pdf_path VARCHAR,
ADD COLUMN IF NOT EXISTS report_excel_path VARCHAR;

-- Comentarios para documentación
COMMENT ON COLUMN audit_reports.report_pdf_path IS 'Ruta al archivo PDF generado del reporte de auditoría';
COMMENT ON COLUMN audit_reports.report_excel_path IS 'Ruta al archivo Excel generado del reporte de auditoría';
COMMENT ON COLUMN audit_comparisons.report_pdf_path IS 'Ruta al archivo PDF generado del reporte de comparación';
COMMENT ON COLUMN audit_comparisons.report_excel_path IS 'Ruta al archivo Excel generado del reporte de comparación';

