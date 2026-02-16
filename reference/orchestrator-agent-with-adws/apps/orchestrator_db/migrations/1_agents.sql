-- ============================================================================
-- AGENTS TABLE
-- ============================================================================
-- Agent registry and configuration for managed agents
--
-- Dependencies: None
-- Note: Each agent has a unique name and tracks its own usage/costs

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    model TEXT NOT NULL,
    system_prompt TEXT,
    working_dir TEXT,
    git_worktree TEXT,
    status TEXT CHECK (status IN ('idle', 'executing', 'waiting', 'blocked', 'complete')),
    session_id TEXT,
    adw_id TEXT,
    adw_step TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0.0000,
    archived BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: agent name must be unique per orchestrator
    CONSTRAINT unique_agent_name_per_orchestrator UNIQUE (orchestrator_agent_id, name)
);

-- Table and column comments
COMMENT ON TABLE agents IS 'Agent registry and configuration for managed agents (scoped to orchestrator)';
COMMENT ON COLUMN agents.id IS 'Unique agent identifier';
COMMENT ON COLUMN agents.orchestrator_agent_id IS 'Foreign key to orchestrator_agents table (required - agents belong to one orchestrator)';
COMMENT ON COLUMN agents.name IS 'Agent name (unique per orchestrator)';
COMMENT ON COLUMN agents.model IS 'Claude model ID (e.g., claude-sonnet-4-5-20250929)';
COMMENT ON COLUMN agents.system_prompt IS 'Agent custom system prompt';
COMMENT ON COLUMN agents.working_dir IS 'Agent working directory path';
COMMENT ON COLUMN agents.git_worktree IS 'Git worktree path if using worktrees';
COMMENT ON COLUMN agents.status IS 'Current status: idle, executing, waiting, blocked, complete';
COMMENT ON COLUMN agents.session_id IS 'Current Claude SDK session ID';
COMMENT ON COLUMN agents.adw_id IS 'AI Developer Workflow ID';
COMMENT ON COLUMN agents.adw_step IS 'AI Developer Workflow step identifier';
COMMENT ON COLUMN agents.input_tokens IS 'Cumulative input tokens consumed';
COMMENT ON COLUMN agents.output_tokens IS 'Cumulative output tokens generated';
COMMENT ON COLUMN agents.total_cost IS 'Cumulative cost in USD (from ResultMessage.usage.total_cost_usd)';
COMMENT ON COLUMN agents.archived IS 'Soft delete flag';
COMMENT ON COLUMN agents.metadata IS 'Agent configuration: allowed_tools, permission_mode, etc. (JSONB)';
