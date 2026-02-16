-- LAI Session Manager - Database Initialization
-- ============================================
--
-- PURPOSE:
-- This script enables PostgreSQL extensions required by the application.
-- It runs automatically when the PostgreSQL container starts for the first time
-- (mounted to /docker-entrypoint-initdb.d/ via docker-compose.yml).
--
-- WHY THIS EXISTS (vs Alembic):
-- PostgreSQL extensions must be enabled at the database level BEFORE any
-- tables or migrations can use them. Alembic manages table schemas, but
-- cannot enable database-level extensions. This script handles what Alembic
-- cannot:
--   1. uuid-ossp  - Required for UUID primary keys in our models
--   2. pg_trgm    - Required for fuzzy text search on session fields
--
-- INITIALIZATION ORDER:
--   1. Docker starts PostgreSQL container
--   2. This script runs (enables extensions)
--   3. FastAPI starts → init_db() creates tables from SQLModel metadata
--   4. Alembic manages future schema migrations (when needed)
--
-- This script is idempotent (safe to run multiple times).

-- ===================
-- Required Extensions
-- ===================

-- UUID support: enables gen_random_uuid() and uuid_generate_v4()
-- Used by: Session.id, Checkpoint.id, and other primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram indexing: enables similarity searches and LIKE optimization
-- Used by: Fuzzy search on session titles, descriptions, tags
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ===================
-- Initialization Log
-- ===================
DO $$
BEGIN
    RAISE NOTICE 'LAI Session Manager: PostgreSQL extensions initialized';
END $$;
