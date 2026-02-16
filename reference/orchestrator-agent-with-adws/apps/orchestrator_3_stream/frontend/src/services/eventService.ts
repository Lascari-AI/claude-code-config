/**
 * Event Service
 *
 * HTTP service for fetching event history from the backend /get_events endpoint.
 * Handles retrieval of agent_logs, system_logs, and orchestrator_chat entries.
 */

import { apiClient } from './api'

// Unified event type with sourceType discriminator
export interface UnifiedEvent {
  sourceType: 'agent_log' | 'system_log' | 'orchestrator_chat'
  [key: string]: any
}

// Response from /get_events endpoint
export interface EventsResponse {
  status: string
  events: UnifiedEvent[]
  count: number
}

// Query parameters for /get_events
export interface GetEventsParams {
  agent_id?: string
  task_slug?: string
  event_types?: string  // "all" or comma-separated: "agent_logs,system_logs,orchestrator_chat"
  limit?: number
  offset?: number
}

/**
 * Fetch events from the backend
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Promise resolving to EventsResponse
 */
export async function getEvents(params: GetEventsParams = {}): Promise<EventsResponse> {
  const response = await apiClient.get<EventsResponse>('/get_events', { params })
  return response.data
}
