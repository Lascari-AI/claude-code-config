-- ============================================================================
-- AI_DEVELOPER_WORKFLOWS TABLE
-- ============================================================================
-- Tracks ADW executions in the system
--
-- Dependencies: orchestrator_agents table (FK constraint)
-- Note: The id column serves as the adw_id referenced by agents, agent_logs, system_logs

CREATE TABLE IF NOT EXISTS ai_developer_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID REFERENCES orchestrator_agents(id) ON DELETE CASCADE,

    -- ADW Identification
    adw_name TEXT NOT NULL,  -- Unique name of the ADW (e.g., "feature-auth") named by the orchestrator agent or user
    workflow_type TEXT NOT NULL,  -- Type of workflow from adws/adw_workflows/adw_*.py filename
    description TEXT,  -- Detailed description of the ADW

    -- Status tracking
    status TEXT NOT NULL CHECK (status IN (
        'pending',      -- Not yet started
        'in_progress',  -- Currently executing
        'completed',    -- Successfully finished
        'failed',       -- Failed with errors
        'cancelled'     -- Manually cancelled
    )) DEFAULT 'pending',

    -- Step tracking
    current_step TEXT,  -- Current step slug (references agent_logs.adw_step)
    total_steps INTEGER DEFAULT 0,  -- Total number of steps in workflow
    completed_steps INTEGER DEFAULT 0,  -- Number of completed steps

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,  -- Total duration (calculated on completion)

    -- Input/Output
    input_data JSONB DEFAULT '{}'::jsonb,   -- Initial input for the ADW
    output_data JSONB DEFAULT '{}'::jsonb,  -- Final output/result

    -- Error tracking
    error_message TEXT,
    error_step TEXT,  -- Step where error occurred
    error_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,  -- Additional workflow metadata

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE ai_developer_workflows IS 'Tracks AI Developer Workflow executions';
COMMENT ON COLUMN ai_developer_workflows.id IS 'Unique identifier (used as adw_id in other tables)';
COMMENT ON COLUMN ai_developer_workflows.orchestrator_agent_id IS 'Foreign key to orchestrator that kicked off this ADW';
COMMENT ON COLUMN ai_developer_workflows.adw_name IS 'Unique name of the ADW (e.g., "feature-auth")';
COMMENT ON COLUMN ai_developer_workflows.workflow_type IS 'Type of workflow (e.g., feature-development, bug-fix)';
COMMENT ON COLUMN ai_developer_workflows.description IS 'Detailed description of the ADW';
COMMENT ON COLUMN ai_developer_workflows.status IS 'Current status: pending, in_progress, completed, failed, cancelled';
COMMENT ON COLUMN ai_developer_workflows.current_step IS 'Current step slug (matches agent_logs.adw_step)';
COMMENT ON COLUMN ai_developer_workflows.total_steps IS 'Total number of steps in the workflow';
COMMENT ON COLUMN ai_developer_workflows.completed_steps IS 'Number of completed steps';
COMMENT ON COLUMN ai_developer_workflows.started_at IS 'When the workflow started executing';
COMMENT ON COLUMN ai_developer_workflows.completed_at IS 'When the workflow completed';
COMMENT ON COLUMN ai_developer_workflows.duration_seconds IS 'Total duration in seconds';
COMMENT ON COLUMN ai_developer_workflows.input_data IS 'Initial input parameters for the workflow';
COMMENT ON COLUMN ai_developer_workflows.output_data IS 'Final output/artifacts after completion';
COMMENT ON COLUMN ai_developer_workflows.error_message IS 'Error message if workflow failed';
COMMENT ON COLUMN ai_developer_workflows.error_step IS 'Step where error occurred';
COMMENT ON COLUMN ai_developer_workflows.error_count IS 'Number of errors encountered';
COMMENT ON COLUMN ai_developer_workflows.metadata IS 'Additional workflow metadata (JSONB)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_adw_orchestrator ON ai_developer_workflows(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_status ON ai_developer_workflows(status);
CREATE INDEX IF NOT EXISTS idx_adw_workflow_type ON ai_developer_workflows(workflow_type);
CREATE INDEX IF NOT EXISTS idx_adw_created ON ai_developer_workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adw_active ON ai_developer_workflows(orchestrator_agent_id, status)
    WHERE status IN ('pending', 'in_progress');

-- Trigger for updated_at (uses existing function from 6_functions.sql)
DROP TRIGGER IF EXISTS update_ai_developer_workflows_updated_at ON ai_developer_workflows;
CREATE TRIGGER update_ai_developer_workflows_updated_at
    BEFORE UPDATE ON ai_developer_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- UPDATE AGENT_LOGS EVENT_CATEGORY CONSTRAINT
-- ============================================================================
-- Add 'adw_step' to support StepStart/StepEnd events for ADW step boundaries

ALTER TABLE agent_logs
    DROP CONSTRAINT IF EXISTS agent_logs_event_category_check;

ALTER TABLE agent_logs
    ADD CONSTRAINT agent_logs_event_category_check
    CHECK (event_category IN ('hook', 'response', 'adw_step'));

-- Update comment to reflect new category
COMMENT ON COLUMN agent_logs.event_category IS 'Event category: hook, response, or adw_step (for StepStart/StepEnd markers)';
