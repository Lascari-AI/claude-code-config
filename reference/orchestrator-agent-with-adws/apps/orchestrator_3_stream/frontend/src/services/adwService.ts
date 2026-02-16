/**
 * ADW Service
 *
 * Handles API communication for AI Developer Workflows
 */

import { apiClient } from './api'
import type {
  ListAdwsResponse,
  GetAdwResponse,
  GetAdwEventsResponse,
  GetAdwSummaryResponse
} from '../types'

/**
 * List AI Developer Workflows for an orchestrator
 */
export async function listAdws(
  orchestratorAgentId: string,
  status?: string,
  limit: number = 20
): Promise<ListAdwsResponse> {
  const response = await apiClient.post<ListAdwsResponse>('/adws', {
    orchestrator_agent_id: orchestratorAgentId,
    status,
    limit
  })
  return response.data
}

/**
 * Get a single ADW by ID
 */
export async function getAdw(adwId: string): Promise<GetAdwResponse> {
  const response = await apiClient.get<GetAdwResponse>(`/adws/${adwId}`)
  return response.data
}

/**
 * Get events for an ADW (swimlane squares)
 */
export async function getAdwEvents(
  adwId: string,
  limit: number = 2000,
  eventType?: string,
  includePayload: boolean = true
): Promise<GetAdwEventsResponse> {
  const response = await apiClient.post<GetAdwEventsResponse>(`/adws/${adwId}/events`, {
    adw_id: adwId,
    limit,
    event_type: eventType,
    include_payload: includePayload
  })
  return response.data
}

/**
 * Get ADW summary with step breakdown
 */
export async function getAdwSummary(adwId: string): Promise<GetAdwSummaryResponse> {
  const response = await apiClient.get<GetAdwSummaryResponse>(`/adws/${adwId}/summary`)
  return response.data
}
