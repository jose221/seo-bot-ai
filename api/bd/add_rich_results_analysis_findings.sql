ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS analysis_findings JSONB;

COMMENT ON COLUMN rich_results_reports.analysis_findings IS
  'Hallazgos estructurados extraidos del HTML final de Google Rich Results';
