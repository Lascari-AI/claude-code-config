/**
 * Agent TypeScript Interfaces
 *
 * Type definitions matching the backend Agent models.
 */

/**
 * Agent type (workflow role).
 */
export type AgentType =
  | "spec"
  | "plan"
  | "quick-plan"
  | "build"
  | "research"
  | "docs"
  | "debug";

/**
 * Agent execution status.
 */
export type AgentStatus =
  | "pending"
  | "executing"
  | "waiting"
  | "complete"
  | "failed"
  | "interrupted";

/**
 * Lightweight agent info for list views.
 */
export interface AgentSummary {
  id: string;
  agent_type: AgentType;
  name: string | null;
  model_alias: string | null;
  status: AgentStatus;
  checkpoint_id: number | null;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Full agent entity with all fields.
 */
export interface Agent {
  id: string;
  session_id: string;
  agent_type: AgentType;
  name: string | null;
  model: string;
  model_alias: string | null;
  sdk_session_id: string | null;
  system_prompt: string | null;
  working_dir: string | null;
  allowed_tools: string | null;
  status: AgentStatus;
  checkpoint_id: number | null;
  task_group_id: string | null;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  error_message: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Get display label for agent type.
 */
export function getAgentTypeLabel(type: AgentType): string {
  const labels: Record<AgentType, string> = {
    spec: "Spec Agent",
    plan: "Plan Agent",
    "quick-plan": "Quick Plan",
    build: "Build Agent",
    research: "Research Agent",
    docs: "Docs Agent",
    debug: "Debug Agent",
  };
  return labels[type] || type;
}

/**
 * Get status color class for styling.
 */
export function getAgentStatusColor(status: AgentStatus): string {
  const colors: Record<AgentStatus, string> = {
    pending: "bg-gray-100 text-gray-700",
    executing: "bg-blue-100 text-blue-700",
    waiting: "bg-yellow-100 text-yellow-700",
    complete: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    interrupted: "bg-orange-100 text-orange-700",
  };
  return colors[status] || "bg-gray-100 text-gray-700";
}
