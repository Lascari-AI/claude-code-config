/**
 * Agent Service
 *
 * Handles HTTP communication for agent management operations
 */

import { apiClient } from './api'

/**
 * Load all active agents
 */
export async function loadAgents() {
  const response = await apiClient.get('/list_agents')
  return response.data.agents
}
