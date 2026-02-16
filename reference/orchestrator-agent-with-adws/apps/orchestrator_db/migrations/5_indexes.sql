-- ============================================================================
-- INDEXES
-- ============================================================================
-- Performance indexes for all tables
--
-- Dependencies: All tables (0-4) must exist
-- Note: Idempotent - can be run multiple times safely

-- orchestrator_agents indexes
CREATE INDEX IF NOT EXISTS idx_orchestrator_agents_status ON orchestrator_agents(status);
CREATE INDEX IF NOT EXISTS idx_orchestrator_agents_updated_at ON orchestrator_agents(updated_at DESC);

-- agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_archived ON agents(archived);
CREATE INDEX IF NOT EXISTS idx_agents_updated_at ON agents(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

-- prompts indexes
CREATE INDEX IF NOT EXISTS idx_prompts_agent_id ON prompts(agent_id);
CREATE INDEX IF NOT EXISTS idx_prompts_author ON prompts(author);
CREATE INDEX IF NOT EXISTS idx_prompts_timestamp ON prompts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_task_slug ON prompts(task_slug) WHERE task_slug IS NOT NULL;

-- agent_logs indexes
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_task_slug ON agent_logs(task_slug) WHERE task_slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_logs_adw_id ON agent_logs(adw_id) WHERE adw_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_logs_adw_step ON agent_logs(adw_step) WHERE adw_step IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_logs_task_index ON agent_logs(task_slug, entry_index) WHERE task_slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_logs_category ON agent_logs(event_category);
CREATE INDEX IF NOT EXISTS idx_agent_logs_type ON agent_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_agent_logs_category_type ON agent_logs(event_category, event_type);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id) WHERE session_id IS NOT NULL;

-- system_logs indexes
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_adw_id ON system_logs(adw_id) WHERE adw_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_system_logs_adw_step ON system_logs(adw_step) WHERE adw_step IS NOT NULL;
