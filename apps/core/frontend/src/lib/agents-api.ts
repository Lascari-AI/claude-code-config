/**
 * Agents API Client
 *
 * Typed API functions for agent and log operations.
 * Uses local Next.js API routes with direct Drizzle database access.
 */

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
 * Uses local Next.js API route with direct Drizzle database access.
 *
 * @param agentId - Agent UUID
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const response = await fetch(`/api/agents/${agentId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Agent ${agentId} not found`);
    }
    throw new Error(`Failed to fetch agent: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch logs for an agent.
 *
 * Uses local Next.js API route with direct Drizzle database access.
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

  const response = await fetch(`/api/agents/${agentId}/logs?${params.toString()}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Agent ${agentId} not found`);
    }
    throw new Error(`Failed to fetch agent logs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a specific log entry with full payload.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 *
 * @param agentId - Agent UUID
 * @param logId - Log entry UUID
 */
export async function getAgentLogDetail(
  agentId: string,
  logId: string
): Promise<AgentLog> {
  const response = await fetch(`/api/agents/${agentId}/logs/${logId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Log ${logId} not found for agent ${agentId}`);
    }
    throw new Error(`Failed to fetch agent log: ${response.statusText}`);
  }

  return response.json();
}
