-- ═══════════════════════════════════════════════════════════
-- ORCHESTRATOR_CHAT TABLE
-- ═══════════════════════════════════════════════════════════
--
-- Tracks all conversations in the multi-agent orchestration system.
--
-- Key Features:
-- - Captures 3-way communication: user ↔ orchestrator ↔ command_agents
-- - sender_type and receiver_type provide directionality
-- - Single message field (no split user_message/orchestrator_message)
-- - Nullable agent_id references command agents when involved
-- - Append-only log for full conversation history
-- - JSONB metadata for extensibility
-- - Turn counter derived from row count per orchestrator_agent_id
--
-- Message Flow Examples:
-- - user → orchestrator: sender='user', receiver='orchestrator', agent_id=NULL
-- - orchestrator → user: sender='orchestrator', receiver='user', agent_id=NULL
-- - orchestrator → agent: sender='orchestrator', receiver='agent', agent_id=builder_id
-- - agent → orchestrator: sender='agent', receiver='orchestrator', agent_id=builder_id
--
-- Dependencies:
-- - orchestrator_agents table (FK: orchestrator_agent_id)
-- - agents table (FK: agent_id - nullable)
--
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS orchestrator_chat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key to orchestrator agent (required)
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,

    -- Sender and receiver (required)
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'orchestrator', 'agent')),
    receiver_type TEXT NOT NULL CHECK (receiver_type IN ('user', 'orchestrator', 'agent')),

    -- Message content (required)
    message TEXT NOT NULL,

    -- AI-generated summary (optional)
    summary TEXT,

    -- Foreign key to command agent (nullable - only when sender or receiver is 'agent')
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,

    -- Extensible metadata storage
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraint: agent_id must be set when sender_type or receiver_type is 'agent'
    CONSTRAINT agent_id_required_for_agents CHECK (
        (sender_type = 'agent' OR receiver_type = 'agent') = (agent_id IS NOT NULL)
    )
);

-- ═══════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════

-- Index for querying by orchestrator_agent_id (for conversation history)
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_orch_id ON orchestrator_chat(orchestrator_agent_id);

-- Index for querying by agent_id (for command agent message history)
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_agent_id ON orchestrator_chat(agent_id);

-- Index for querying by sender_type (for filtering by sender)
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_sender_type ON orchestrator_chat(sender_type);

-- Index for querying by receiver_type (for filtering by receiver)
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_receiver_type ON orchestrator_chat(receiver_type);

-- Composite index for ordered conversation retrieval
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_orch_created ON orchestrator_chat(orchestrator_agent_id, created_at DESC);

-- Composite index for agent conversation retrieval
CREATE INDEX IF NOT EXISTS idx_orchestrator_chat_agent_created ON orchestrator_chat(agent_id, created_at DESC);

-- ═══════════════════════════════════════════════════════════
-- COMMENTS
-- ═══════════════════════════════════════════════════════════

COMMENT ON TABLE orchestrator_chat IS
    'Append-only conversation log capturing 3-way communication: user ↔ orchestrator ↔ agents. Turn counter derived from row count per orchestrator_agent_id.';

COMMENT ON COLUMN orchestrator_chat.orchestrator_agent_id IS
    'Foreign key to orchestrator_agents table (required)';

COMMENT ON COLUMN orchestrator_chat.sender_type IS
    'Who sent this message: user, orchestrator, or agent';

COMMENT ON COLUMN orchestrator_chat.receiver_type IS
    'Who receives this message: user, orchestrator, or agent';

COMMENT ON COLUMN orchestrator_chat.message IS
    'The message text content';

COMMENT ON COLUMN orchestrator_chat.summary IS
    'AI-generated 1-sentence summary of the message (50-100 chars)';

COMMENT ON COLUMN orchestrator_chat.agent_id IS
    'Foreign key to agents table (required when sender_type or receiver_type is agent, NULL otherwise)';

COMMENT ON COLUMN orchestrator_chat.metadata IS
    'Extensible JSONB field for additional context (tools_used, task_slug, etc)';
