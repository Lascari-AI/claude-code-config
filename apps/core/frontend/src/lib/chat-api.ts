/**
 * Chat API Client
 *
 * Typed API functions for interactive chat with the FastAPI backend.
 * Communicates with the /chat endpoints on the Python backend.
 */

import { fetchApi } from "./api";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * A single response block from the agent.
 */
export interface ChatBlock {
  role: string;
  block_type: string;
  content: string | null;
  tool_name: string | null;
}

/**
 * Response from the send-message endpoint.
 */
export interface ChatSendResponse {
  blocks: ChatBlock[];
  turn_index: number;
}

/**
 * A single message block from chat history.
 * Includes turn/block indices and timestamp for ordering.
 */
export interface ChatHistoryMessage {
  role: string;
  block_type: string;
  content: string | null;
  tool_name: string | null;
  turn_index: number;
  block_index: number;
  timestamp: string;
}

/**
 * Response from the chat history endpoint.
 */
export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
  total: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Send a message to the spec interview agent.
 *
 * Posts to the FastAPI backend /chat/send endpoint.
 * Returns agent response blocks for rendering in the chat panel.
 *
 * @param sessionSlug - Session identifier
 * @param message - User message text
 * @returns Agent response blocks and turn index
 */
export async function sendMessage(
  sessionSlug: string,
  message: string
): Promise<ChatSendResponse> {
  return fetchApi<ChatSendResponse>("/chat/send", {
    method: "POST",
    body: JSON.stringify({
      session_slug: sessionSlug,
      message,
    }),
  });
}

/**
 * Get chat history for a session.
 *
 * Fetches persisted messages from the backend history endpoint,
 * ordered by turn_index then block_index.
 *
 * @param sessionSlug - Session identifier
 * @param phase - Optional phase filter (spec, plan)
 * @returns Chat history messages and total count
 */
export async function getChatHistory(
  sessionSlug: string,
  phase?: string
): Promise<ChatHistoryResponse> {
  const params = new URLSearchParams();
  if (phase) params.set("phase", phase);
  const query = params.toString();
  const endpoint = `/chat/history/${sessionSlug}${query ? `?${query}` : ""}`;

  return fetchApi<ChatHistoryResponse>(endpoint);
}
