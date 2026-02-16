-- ============================================================================
-- TRIGGERS
-- ============================================================================
-- Automatic triggers for timestamp updates
--
-- Dependencies: Functions from 6_functions.sql must exist
-- Note: Idempotent - DROP IF EXISTS + CREATE allows safe re-runs

-- Trigger for orchestrator_agents updated_at
DROP TRIGGER IF EXISTS update_orchestrator_agents_updated_at ON orchestrator_agents;
CREATE TRIGGER update_orchestrator_agents_updated_at
  BEFORE UPDATE ON orchestrator_agents
  FOR EACH ROW
  EXECUTE FUNCTION update_orchestrator_updated_at();

-- Trigger for agents updated_at
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW
  EXECUTE FUNCTION update_agents_updated_at();
