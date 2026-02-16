-- ============================================================================
-- PROMPTS TABLE
-- ============================================================================
-- Prompts sent to agents (from engineers or orchestrator agent)
--
-- Dependencies: agents table (FK constraint)
-- Note: Cascades on delete when agent is removed

CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    task_slug TEXT,
    author TEXT NOT NULL CHECK (author IN ('engineer', 'orchestrator_agent')),
    prompt_text TEXT NOT NULL,
    summary TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id TEXT
);

-- Table and column comments
COMMENT ON TABLE prompts IS 'Prompts sent to agents from engineers or orchestrator';
COMMENT ON COLUMN prompts.id IS 'Unique prompt identifier';
COMMENT ON COLUMN prompts.agent_id IS 'Target agent receiving the prompt (nullable, only populated when author = orchestrator_agent)';
COMMENT ON COLUMN prompts.task_slug IS 'Associated task identifier (kebab-case)';
COMMENT ON COLUMN prompts.author IS 'Who sent the prompt: engineer or orchestrator_agent';
COMMENT ON COLUMN prompts.prompt_text IS 'The actual prompt content';
COMMENT ON COLUMN prompts.summary IS 'AI-generated 1-sentence summary of the prompt (50-100 chars)';
COMMENT ON COLUMN prompts.timestamp IS 'When the prompt was sent';
COMMENT ON COLUMN prompts.session_id IS 'Claude SDK session ID';
