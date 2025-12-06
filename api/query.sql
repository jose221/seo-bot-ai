-- 1. CONFIGURACIÓN INICIAL
--Crear bd si no existe
--DATABASE seo_bot_db;
-- Habilitar extensión para generar UUIDs si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear tipos de datos personalizados (ENUMS) para mantener consistencia
CREATE TYPE target_status_enum AS ENUM ('ACTIVE', 'ARCHIVED', 'PAUSED');
CREATE TYPE audit_status_enum AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

-- ==========================================
-- 2. TABLA: USERS (Shadow User)
-- ==========================================
-- Esta tabla refleja al usuario de Herandro API.
-- No guardamos password aquí.
CREATE TABLE users (
                       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- IDs y datos externos (Vienen de la API de Auth)
                       external_id UUID NOT NULL UNIQUE, -- El user_id de la API externa
                       email VARCHAR(255) NOT NULL,
                       full_name VARCHAR(255),
                       tenant_id UUID NOT NULL,          -- Para contexto de multi-tenencia
                       project_id UUID,                  -- Contexto del proyecto actual

    -- Auditoría interna
                       last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para búsqueda rápida en el Middleware de Auth
CREATE INDEX idx_users_external_id ON users(external_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_project_id ON users(project_id);


-- ==========================================
-- 3. TABLA: WEB_PAGES (Targets)
-- ==========================================
-- Los sitios que vamos a auditar.
CREATE TABLE web_pages (
                           id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relación con el usuario (Dueño del target)
                           user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Datos del objetivo
                           url TEXT NOT NULL,
                           tech_stack VARCHAR(255),     -- Ej: "Wordpress", "React" (Ayuda a la IA)
                           instructions TEXT,           -- Prompt de navegación: "Logueate y ve al carrito..."

                           status target_status_enum DEFAULT 'ACTIVE',

                           created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                           updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para listar rápidamente los sitios de un usuario/proyecto
CREATE INDEX idx_web_pages_user_id ON web_pages(user_id);


-- ==========================================
-- 4. TABLA: AUDIT_REPORTS (Resultados)
-- ==========================================
-- Aquí se guarda la "magia": JSONs gigantes de Lighthouse y análisis de IA.
CREATE TABLE audit_reports (
                               id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relación con la página web
                               web_page_id UUID NOT NULL REFERENCES web_pages(id) ON DELETE CASCADE,

    -- Estado del proceso (controlado por el Worker)
                               status audit_status_enum DEFAULT 'PENDING',

    -- 1. Datos Cuantitativos (Lighthouse)
    -- Usamos JSONB para consultas rápidas dentro del JSON si fuera necesario
                               lighthouse_data JSONB,

    -- 2. Datos Cualitativos (IA + Análisis Semántico)
                               ai_analysis JSONB,     -- Sugerencias, Score de afinidad, análisis UX

    -- Logs de ejecución (útil si falló Playwright)
                               navigation_log JSONB,
                               error_message TEXT,

    -- Tiempos
                               created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Cuándo se pidió
                               completed_at TIMESTAMP WITH TIME ZONE              -- Cuándo terminó el worker
);

-- Índice para buscar reportes por página y fecha
CREATE INDEX idx_audit_reports_web_page_id ON audit_reports(web_page_id);
CREATE INDEX idx_audit_reports_created_at ON audit_reports(created_at DESC);

-- ==========================================
-- 5. COMENTARIOS DE DOCUMENTACIÓN
-- ==========================================
COMMENT ON TABLE users IS 'Copia local de usuarios validados por Herandro API';
COMMENT ON COLUMN users.external_id IS 'UUID original proveniente del Identity Provider externo';
COMMENT ON COLUMN audit_reports.lighthouse_data IS 'Almacena el JSON crudo filtrado de la auditoría de Google Lighthouse';
COMMENT ON COLUMN audit_reports.ai_analysis IS 'Almacena sugerencias generadas por DeepSeek/LLM sobre estructura y SEO';