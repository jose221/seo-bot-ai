ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'pending';

ALTER TABLE rich_results_reports
  ADD COLUMN IF NOT EXISTS requested_ai_result BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_rich_results_reports_status
  ON rich_results_reports(status);

UPDATE rich_results_reports
SET status = 'completed'
WHERE status IS NULL OR status = '';
