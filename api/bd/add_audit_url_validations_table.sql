-- Crear tabla de validaciones de schemas por URL
CREATE TABLE IF NOT EXISTS audit_url_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Referencia al origen
    source_type VARCHAR NOT NULL,
    source_id UUID NOT NULL,

    -- Parámetros de la validación
    name_validation VARCHAR(255) NOT NULL,
    description_validation TEXT,
    ai_instruction TEXT,
    urls_raw TEXT,

    -- Estado
    status VARCHAR NOT NULL DEFAULT 'pending',

    -- Severidad global (peor caso entre todas las URLs)
    global_severity VARCHAR,

    -- Resultado completo como JSON
    results_json JSONB,

    -- Reportes
    report_pdf_path VARCHAR,
    report_word_path VARCHAR,

    -- Tokens
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,

    -- Metadata
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_audit_url_validations_user_id ON audit_url_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_url_validations_source_type ON audit_url_validations(source_type);
CREATE INDEX IF NOT EXISTS idx_audit_url_validations_source_id ON audit_url_validations(source_id);
CREATE INDEX IF NOT EXISTS idx_audit_url_validations_status ON audit_url_validations(status);

