
-- 1. Crear el usuario (Rol)
-- Cambia 'tu_password_seguro_123' por la contraseña que quieras usar realmente
CREATE USER seo_bot_user WITH PASSWORD 'Gonzales220';

-- 2. Conceder permisos sobre la base de datos específica
GRANT ALL PRIVILEGES ON DATABASE seo_bot_db TO seo_bot_user;

-- 3. (Importante para PostgreSQL 15+) Conceder permisos en el esquema public
-- Nos conectamos a la base de datos específica primero (si lo haces por script, esto es implícito al dar ALL PRIVILEGES, pero aseguremos el esquema)
\c seo_bot_db

-- Permitir que cree tablas en el esquema public
GRANT USAGE, CREATE ON SCHEMA public TO seo_bot_user;

-- 4. Asegurar permisos para el futuro (Default Privileges)
-- Esto asegura que las tablas que cree el ORM sean accesibles y modificables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO seo_bot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO seo_bot_user;

drop table audit_reports;

-- 1. Borramos el tipo anterior y todo lo que dependa de él (limpieza total)
DROP TYPE IF EXISTS audit_status_enum CASCADE;

-- 2. Lo creamos coincidiendo con el VALOR de tu Python ("pending", no PENDING)
CREATE TYPE audit_status_enum AS ENUM (
    'PENDING',      -- Coincide con PENDING = "pending"
    'IN_PROGRESS',  -- Coincide con IN_PROGRESS = "in_progress"
    'COMPLETED',    -- Coincide con COMPLETED = "completed"
    'FAILED'        -- Coincide con FAILED = "failed"
    );

-- 3. (Opcional) Si borraste la tabla audit_reports por el CASCADE, recréala:
CREATE TABLE IF NOT EXISTS audit_reports (
                                             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                             web_page_id UUID NOT NULL REFERENCES web_pages(id) ON DELETE CASCADE,
                                             user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                                             status TEXT DEFAULT 'PENDING', -- Valor por defecto también en minúscula
                                             lighthouse_data JSONB,
                                             ai_suggestions JSONB,
                                             performance_score DOUBLE PRECISION,
                                             seo_score DOUBLE PRECISION,
                                             accessibility_score DOUBLE PRECISION,
                                             best_practices_score DOUBLE PRECISION,
                                             lcp DOUBLE PRECISION,
                                             fid DOUBLE PRECISION,
                                             cls DOUBLE PRECISION,
                                             error_message TEXT,
                                             created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                             completed_at TIMESTAMP WITH TIME ZONE
);