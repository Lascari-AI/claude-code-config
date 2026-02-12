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


// ═══════════════════════════════════════════════════════════════════════════════
// AGENT LOG TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Event categories for agent logs.
 */
export type EventCategory = "hook" | "response" | "phase";

/**
 * Lightweight log entry for timeline views.
 */
export interface AgentLogSummary {
  id: string;
  agent_id: string;
  session_id: string;
  event_category: EventCategory;
  event_type: string;
  tool_name: string | null;
  content: string | null;
  summary: string | null;
  timestamp: string;
  duration_ms: number | null;
}

/**
 * Full agent log entry with payload.
 */
export interface AgentLog extends AgentLogSummary {
  sdk_session_id: string | null;
  payload: Record<string, unknown>;
  tool_input: string | null;
  tool_output: string | null;
  entry_index: number | null;
  checkpoint_id: number | null;
}

/**
 * Get display label for event category.
 */
export function getEventCategoryLabel(category: EventCategory): string {
  const labels: Record<EventCategory, string> = {
    hook: "Hook Event",
    response: "Response",
    phase: "Phase Transition",
  };
  return labels[category] || category;
}

/**
 * Get event category color class for styling.
 */
export function getEventCategoryColor(category: EventCategory): string {
  const colors: Record<EventCategory, string> = {
    hook: "bg-blue-100 text-blue-700 border-blue-200",
    response: "bg-purple-100 text-purple-700 border-purple-200",
    phase: "bg-green-100 text-green-700 border-green-200",
  };
  return colors[category] || "bg-gray-100 text-gray-700 border-gray-200";
}

/**
 * Get specific event type color (for tool names, etc.)
 */
export function getEventTypeColor(eventType: string): string {
  // Tool-related events
  if (eventType === "PreToolUse" || eventType === "PostToolUse") {
    return "bg-cyan-100 text-cyan-700";
  }
  if (eventType === "ToolError") {
    return "bg-red-100 text-red-700";
  }
  // Notifications and stops
  if (eventType === "Notification") {
    return "bg-yellow-100 text-yellow-700";
  }
  if (eventType === "Stop") {
    return "bg-gray-100 text-gray-700";
  }
  // Default
  return "bg-gray-100 text-gray-700";
}
