-- Agregar mensaje de progreso y bitácora persistida para tareas masivas

ALTER TABLE audit_url_validations
    ADD COLUMN IF NOT EXISTS progress_message TEXT;

ALTER TABLE audit_comparisons
    ADD COLUMN IF NOT EXISTS progress_message TEXT;

ALTER TABLE rich_results_reports
    ADD COLUMN IF NOT EXISTS progress_message TEXT;

CREATE TABLE IF NOT EXISTS task_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(80) NOT NULL,
    task_id UUID NOT NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    progress_percentage INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_execution_logs_task_type_task_id
    ON task_execution_logs(task_type, task_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_execution_logs_created_at
    ON task_execution_logs(created_at DESC);

COMMENT ON COLUMN audit_url_validations.progress_message IS 'Ultimo mensaje visible del avance de la validación URL';
COMMENT ON COLUMN audit_comparisons.progress_message IS 'Ultimo mensaje visible del avance de la comparación';
COMMENT ON COLUMN rich_results_reports.progress_message IS 'Ultimo mensaje visible del avance del reporte Rich Results';
COMMENT ON TABLE task_execution_logs IS 'Bitácora persistida de progreso, warnings y errores de tareas batch';
