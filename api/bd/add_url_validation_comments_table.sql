-- Tabla de comentarios públicos vinculados a una URL dentro de una validación
CREATE TABLE IF NOT EXISTS url_validation_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Referencia a la validación (audit_url_validations)
    validation_id UUID NOT NULL REFERENCES audit_url_validations(id) ON DELETE CASCADE,

    -- URL del schema item al que pertenece el comentario
    schema_item_url TEXT NOT NULL,

    -- Datos del comentarista (público, sin cuenta)
    username VARCHAR(150) NOT NULL,
    comment TEXT NOT NULL,

    -- Estado del comentario
    -- pending  → recién creado, sin respuesta
    -- done     → respondido/resuelto
    -- rejected → rechazado por el administrador
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Respuesta del usuario dueño de la validación
    answer TEXT,
    answered_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_url_val_comments_validation_id ON url_validation_comments(validation_id);
CREATE INDEX IF NOT EXISTS idx_url_val_comments_schema_item   ON url_validation_comments(schema_item_url);
CREATE INDEX IF NOT EXISTS idx_url_val_comments_status        ON url_validation_comments(status);
