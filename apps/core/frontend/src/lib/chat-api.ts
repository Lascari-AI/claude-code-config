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
