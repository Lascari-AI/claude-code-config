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
 * Structured question from AskUserQuestion tool call.
 */
export interface PendingQuestion {
  tool_use_id: string;
  questions: Array<{
    question: string;
    header: string;
    options: Array<{ label: string; description: string }>;
    multiSelect: boolean;
  }>;
}

/**
 * Response from the send-message and answer endpoints.
 */
export interface ChatSendResponse {
  blocks: ChatBlock[];
  turn_index: number;
  pending_question: PendingQuestion | null;
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

/**
 * Submit user's answer to an AskUserQuestion tool call.
 *
 * Posts the user's selection(s) to the backend /chat/answer endpoint,
 * which routes the tool result back to the SDK agent.
 *
 * @param sessionSlug - Session identifier
 * @param toolUseId - The tool_use_id from the pending question
 * @param answers - Answer selections {question_text: selected_option}
 * @returns Agent response blocks (may contain another pending_question)
 */
export async function sendAnswer(
  sessionSlug: string,
  toolUseId: string,
  answers: Record<string, string>
): Promise<ChatSendResponse> {
  return fetchApi<ChatSendResponse>("/chat/answer", {
    method: "POST",
    body: JSON.stringify({
      session_slug: sessionSlug,
      tool_use_id: toolUseId,
      answers,
    }),
  });
}
