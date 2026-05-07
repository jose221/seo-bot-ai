-- Crear tabla para persistir reportes de Google Rich Results
CREATE TABLE IF NOT EXISTS rich_results_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    progress_message TEXT,
    input_type VARCHAR NOT NULL,
    requested_ai_result BOOLEAN NOT NULL DEFAULT FALSE,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    method_used VARCHAR NOT NULL,
    result_url TEXT,
    message TEXT NOT NULL,
    error_message TEXT,
    blocked_by_google BOOLEAN NOT NULL DEFAULT FALSE,
    screenshots JSONB,
    ai_result_content TEXT,
    ai_result_usage JSONB,
    ai_result_model VARCHAR,
    ai_generated_at VARCHAR,
    ai_error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rich_results_reports_user_id ON rich_results_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_rich_results_reports_url ON rich_results_reports(url);
CREATE INDEX IF NOT EXISTS idx_rich_results_reports_status ON rich_results_reports(status);
CREATE INDEX IF NOT EXISTS idx_rich_results_reports_created_at ON rich_results_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_rich_results_reports_user_url_created_at
    ON rich_results_reports(user_id, url, created_at DESC);
