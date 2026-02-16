-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================
-- Functions used by triggers for automatic timestamp updates
--
-- Dependencies: orchestrator_agents and agents tables must exist
-- Note: Idempotent - CREATE OR REPLACE allows safe re-runs

-- Auto-update updated_at timestamp on orchestrator_agents
CREATE OR REPLACE FUNCTION update_orchestrator_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Auto-update updated_at timestamp on agents
CREATE OR REPLACE FUNCTION update_agents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
