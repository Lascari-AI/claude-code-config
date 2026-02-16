-- ============================================================================
-- ORCHESTRATOR_AGENTS TABLE
-- ============================================================================
-- The orchestrator agent that manages other agents
--
-- Dependencies: None
-- Constraints:
--   - session_id must be unique (prevents duplicate sessions)

-- Create table with UNIQUE constraint on session_id (idempotent)
CREATE TABLE IF NOT EXISTS orchestrator_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE,  -- UNIQUE constraint prevents duplicate session IDs
    system_prompt TEXT,
    status TEXT CHECK (status IN ('idle', 'executing', 'waiting', 'blocked', 'complete')),
    working_dir TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0000,
    archived BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE orchestrator_agents IS 'Orchestrator agents that manage other agents';
COMMENT ON COLUMN orchestrator_agents.id IS 'Unique orchestrator identifier';
COMMENT ON COLUMN orchestrator_agents.session_id IS 'Unique Claude SDK session ID (NULL until first interaction)';
COMMENT ON COLUMN orchestrator_agents.system_prompt IS 'Orchestrator system prompt';
COMMENT ON COLUMN orchestrator_agents.status IS 'Current status: idle, executing, waiting, blocked, complete';
COMMENT ON COLUMN orchestrator_agents.working_dir IS 'Orchestrator working directory';
COMMENT ON COLUMN orchestrator_agents.input_tokens IS 'Cumulative input tokens consumed';
COMMENT ON COLUMN orchestrator_agents.output_tokens IS 'Cumulative output tokens generated';
COMMENT ON COLUMN orchestrator_agents.total_cost IS 'Cumulative cost in USD';
COMMENT ON COLUMN orchestrator_agents.archived IS 'Soft delete flag';
COMMENT ON COLUMN orchestrator_agents.metadata IS 'Orchestrator configuration (JSONB)';
