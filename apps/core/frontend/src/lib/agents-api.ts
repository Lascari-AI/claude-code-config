/**
 * Agents API Client
 *
 * Typed API functions for agent and log operations.
 */

import { fetchApi } from "./api";
import type { Agent, AgentLogSummary, AgentLog } from "@/types/agent";

/**
 * Filter options for listing agent logs.
 */
export interface AgentLogFilters {
  eventCategory?: string;
  eventType?: string;
  limit?: number;
  offset?: number;
}

/**
 * Fetch an agent by ID.
 *
 * @param agentId - Agent UUID
 */
export async function getAgent(agentId: string): Promise<Agent> {
  return fetchApi<Agent>(`/agents/${agentId}`);
}

/**
 * Fetch logs for an agent.
 *
 * @param agentId - Agent UUID
 * @param filters - Optional filter parameters
 */
export async function getAgentLogs(
  agentId: string,
  filters: AgentLogFilters = {}
): Promise<AgentLogSummary[]> {
  const params = new URLSearchParams();

  if (filters.eventCategory) params.set("event_category", filters.eventCategory);
  if (filters.eventType) params.set("event_type", filters.eventType);
  params.set("limit", String(filters.limit ?? 100));
  params.set("offset", String(filters.offset ?? 0));

  const query = params.toString();
  return fetchApi<AgentLogSummary[]>(`/agents/${agentId}/logs?${query}`);
}

/**
 * Fetch a specific log entry with full payload.
 *
 * @param agentId - Agent UUID
 * @param logId - Log entry UUID
 */
export async function getAgentLogDetail(
  agentId: string,
  logId: string
): Promise<AgentLog> {
  return fetchApi<AgentLog>(`/agents/${agentId}/logs/${logId}`);
}
