-- LAI Session Manager - Database Initialization
--
-- This script runs automatically when the PostgreSQL container starts
-- for the first time. It sets up extensions and any initial configuration.

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for fuzzy text search (useful for searching sessions)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'LAI Session Manager database initialized';
END $$;
