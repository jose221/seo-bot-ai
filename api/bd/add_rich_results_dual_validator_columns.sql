ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS validate_google BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS validate_schema_org BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS google_validation_result JSONB;

ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS schema_org_validation_result JSONB;

COMMENT ON COLUMN rich_results_reports.google_validation_result IS
  'Detalle completo del validador Google Rich Results';

COMMENT ON COLUMN rich_results_reports.schema_org_validation_result IS
  'Detalle completo del validador Schema.org';
