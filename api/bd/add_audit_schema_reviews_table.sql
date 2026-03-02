-- Tabla para auditoría de schemas (original vs propuesto vs nuevo)
CREATE TABLE IF NOT EXISTS audit_schema_reviews (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    source_type VARCHAR NOT NULL,
    source_id UUID NOT NULL,

    original_schema_json JSON,
    proposed_schema_json JSON,
    incoming_schema_json JSON,

    schema_org_validation_result JSON,
    triple_comparison_result JSON,
    progress_report JSON,

    cqrs_solid_model_text TEXT,

    include_ai_analysis BOOLEAN DEFAULT TRUE,
    programming_language VARCHAR(50),

    status VARCHAR NOT NULL DEFAULT 'pending',

    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,

    report_pdf_path VARCHAR,
    report_word_path VARCHAR,

    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_schema_reviews_user_id ON audit_schema_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_schema_reviews_source_type ON audit_schema_reviews(source_type);
CREATE INDEX IF NOT EXISTS idx_audit_schema_reviews_source_id ON audit_schema_reviews(source_id);
CREATE INDEX IF NOT EXISTS idx_audit_schema_reviews_status ON audit_schema_reviews(status);
