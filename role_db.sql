-- 1. Crear el usuario (Rol)
-- Cambia 'tu_password_seguro_123' por la contraseña que quieras usar realmente
CREATE USER seo_bot_user WITH PASSWORD 'Gonzales220.';

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