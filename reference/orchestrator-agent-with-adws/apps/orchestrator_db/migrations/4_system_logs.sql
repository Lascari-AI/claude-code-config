-- ============================================================================
-- SYSTEM_LOGS TABLE
-- ============================================================================
-- All application logs (global application events only)
--
-- Dependencies: None
-- Note: agent-related logs should go in agent_logs table

CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT,
    adw_id TEXT,
    adw_step TEXT,
    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE system_logs IS 'Application-level system logs (global application events only)';
COMMENT ON COLUMN system_logs.id IS 'Unique log entry identifier';
COMMENT ON COLUMN system_logs.file_path IS 'Associated file path where log was written';
COMMENT ON COLUMN system_logs.adw_id IS 'Associated ADW identifier';
COMMENT ON COLUMN system_logs.adw_step IS 'AI Developer Workflow step identifier';
COMMENT ON COLUMN system_logs.level IS 'Log level: DEBUG, INFO, WARNING, ERROR';
COMMENT ON COLUMN system_logs.message IS 'Log message';
COMMENT ON COLUMN system_logs.summary IS 'AI-generated 1-sentence summary of the log message (50-100 chars)';
COMMENT ON COLUMN system_logs.metadata IS 'Additional log context (JSONB)';
COMMENT ON COLUMN system_logs.timestamp IS 'When the log was created';
