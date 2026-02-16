-- ============================================================================
-- AGENT_LOGS TABLE
-- ============================================================================
-- Unified event log - all hook events and agent responses during task execution
-- Combines operator logs (JSONL-style task tracking), hook events, and agent response blocks
--
-- Dependencies: agents table (FK constraint)
-- Note: Cascades on delete when agent is removed

CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    session_id TEXT,
    task_slug TEXT,
    adw_id TEXT,
    adw_step TEXT,
    entry_index INTEGER,
    event_category TEXT NOT NULL CHECK (event_category IN ('hook', 'response')),
    event_type TEXT NOT NULL,
    content TEXT,
    payload JSONB DEFAULT '{}'::jsonb,
    summary TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE agent_logs IS 'Unified event log for hooks and agent responses during task execution';
COMMENT ON COLUMN agent_logs.id IS 'Unique log entry identifier';
COMMENT ON COLUMN agent_logs.agent_id IS 'Agent that generated this event';
COMMENT ON COLUMN agent_logs.session_id IS 'Claude SDK session ID';
COMMENT ON COLUMN agent_logs.task_slug IS 'Task identifier (kebab-case)';
COMMENT ON COLUMN agent_logs.adw_id IS 'AI Developer Workflow identifier';
COMMENT ON COLUMN agent_logs.adw_step IS 'AI Developer Workflow step identifier';
COMMENT ON COLUMN agent_logs.entry_index IS 'Sequential index within task for tail reading';
COMMENT ON COLUMN agent_logs.event_category IS 'Event category: hook or response';
COMMENT ON COLUMN agent_logs.event_type IS 'Specific event type - For hooks: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact; For responses: text, thinking, tool_use, tool_result';
COMMENT ON COLUMN agent_logs.content IS 'Text content for text/thinking blocks';
COMMENT ON COLUMN agent_logs.payload IS 'Complete event data (tool info, block details, etc.) as JSONB';
COMMENT ON COLUMN agent_logs.summary IS 'AI-generated summary of this event';
COMMENT ON COLUMN agent_logs.timestamp IS 'When the event occurred';
