/**
 * Autocomplete Service
 *
 * API client for autocomplete functionality
 */

import { apiClient } from './api'
import type {
  AutocompleteGenerateRequest,
  AutocompleteUpdateRequest,
  AutocompleteResponse
} from '../types'

/**
 * Generate autocomplete suggestions based on user input
 *
 * @param userInput - Current user input text
 * @param orchestratorAgentId - Orchestrator agent UUID
 * @returns AutocompleteResponse with list of suggestions
 */
export async function generateAutocomplete(
  userInput: string,
  orchestratorAgentId: string
): Promise<AutocompleteResponse> {
  const response = await apiClient.post<AutocompleteResponse>('/autocomplete-generate', {
    user_input: userInput,
    orchestrator_agent_id: orchestratorAgentId
  })
  return response.data
}

/**
 * Update autocomplete history (track accepted/rejected completions)
 *
 * @param request - AutocompleteUpdateRequest with completion details
 * @returns Success status
 */
export async function updateAutocompleteHistory(
  request: AutocompleteUpdateRequest
): Promise<{ status: string }> {
  const response = await apiClient.post('/autocomplete-update', request)
  return response.data
}
