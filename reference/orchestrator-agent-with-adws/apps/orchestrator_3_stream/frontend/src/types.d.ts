/**
 * TypeScript Type Definitions
 *
 * These types mirror the database models from apps/orchestrator_db/models.py
 * They provide type safety across the frontend application.
 */

// ═══════════════════════════════════════════════════════════
// ORCHESTRATOR_AGENT TYPE
// ═══════════════════════════════════════════════════════════

export type AgentStatus = 'idle' | 'executing' | 'waiting' | 'blocked' | 'complete'

export interface OrchestratorAgent {
  id: string
  session_id: string | null
  system_prompt: string | null
  status: AgentStatus | null
  working_dir: string | null
  input_tokens: number
  output_tokens: number
  total_cost: number
  archived: boolean
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

// ═══════════════════════════════════════════════════════════
// SYSTEM MESSAGE & COMMAND TYPES
// ═══════════════════════════════════════════════════════════

// System Message Metadata
export interface SystemMessageInfo {
  session_id?: string | null
  cwd?: string | null
  tools?: string[]
  model?: string | null
  subtype?: string
  captured_at?: string
}

// Slash Command
export interface SlashCommand {
  name: string
  description: string
  arguments?: string
  model?: string
}

// ADW Workflow
export interface AdwWorkflow {
  type: string
  display_name: string
  description: string
}

// Subagent Template
export interface SubagentFrontmatter {
  name: string
  description: string
  tools?: string[] | null
  model?: string | null
  color?: string | null
}

export interface SubagentTemplate {
  frontmatter: SubagentFrontmatter
  prompt_body: string
  file_path: string
}

// API Response for /get_orchestrator
export interface GetOrchestratorResponse {
  status: string
  orchestrator: OrchestratorAgent
  slash_commands: SlashCommand[]
  agent_templates: SubagentTemplate[]
  orchestrator_tools: string[]  // Tool signatures in TypeScript format
}

// ═══════════════════════════════════════════════════════════
// AGENT TYPE
// ═══════════════════════════════════════════════════════════

export interface AgentMetadata {
  template_name?: string // Name of subagent template used (if created from template)
  template_color?: string // UI color from template
  [key: string]: any // Allow other metadata properties
}

export interface Agent {
  id: string
  name: string
  model: string
  system_prompt: string | null
  working_dir: string | null
  git_worktree: string | null
  status: AgentStatus | null
  session_id: string | null
  adw_id: string | null
  adw_step: string | null
  input_tokens: number
  output_tokens: number
  total_cost: number
  archived: boolean
  metadata: AgentMetadata
  task?: string // Optional task description for UI display
  log_count?: number // Optional log count from backend
  latest_summary?: string // Latest log summary for this agent
  created_at: string
  updated_at: string
}

// ═══════════════════════════════════════════════════════════
// PROMPT TYPE
// ═══════════════════════════════════════════════════════════

export type PromptAuthor = 'engineer' | 'orchestrator_agent'

export interface Prompt {
  id: string
  agent_id: string | null
  task_slug: string | null
  author: PromptAuthor
  prompt_text: string
  timestamp: string
  session_id: string | null
}

// ═══════════════════════════════════════════════════════════
// AGENT_LOG TYPE
// ═══════════════════════════════════════════════════════════

export type EventCategory = 'hook' | 'response'

// File tracking types
export interface FileChange {
  path: string
  absolute_path: string
  status: 'created' | 'modified' | 'deleted'
  lines_added: number
  lines_removed: number
  diff?: string
  summary?: string
  agent_id?: string
  agent_name?: string
}

export interface FileRead {
  path: string
  absolute_path: string
  line_count: number
  agent_id?: string
  agent_name?: string
}

export interface AgentLogMetadata {
  file_changes?: FileChange[]
  read_files?: FileRead[]
  total_files_modified?: number
  total_files_read?: number
  generated_at?: string
}

export interface AgentLog {
  id: string
  agent_id: string
  agent_name?: string  // Optional agent name field
  session_id: string | null
  task_slug: string | null
  entry_index: number | null
  event_category: EventCategory
  event_type: string
  content: string | null
  payload: AgentLogMetadata | Record<string, any>
  summary: string | null
  timestamp: string
}

// ═══════════════════════════════════════════════════════════
// SYSTEM_LOG TYPE
// ═══════════════════════════════════════════════════════════

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'

export interface SystemLog {
  id: string
  agent_id: string | null
  file_path: string | null
  adw_id: string | null
  level: LogLevel
  message: string
  metadata: Record<string, any>
  timestamp: string
}

// ═══════════════════════════════════════════════════════════
// ORCHESTRATOR_CHAT TYPE
// ═══════════════════════════════════════════════════════════

export type ParticipantType = 'user' | 'orchestrator' | 'agent'

export interface OrchestratorChat {
  id: string
  created_at: string
  updated_at: string
  orchestrator_agent_id: string
  sender_type: ParticipantType
  receiver_type: ParticipantType
  message: string
  agent_id: string | null
  metadata: Record<string, any>
}

// ═══════════════════════════════════════════════════════════
// UI-SPECIFIC TYPES
// ═══════════════════════════════════════════════════════════

// Extended agent with computed fields for UI
export interface AgentWithStats extends Agent {
  logCount?: number
  isActive?: boolean
}

// Event stream filter types
export type EventStreamFilter = 'all' | 'errors' | 'hooks' | 'responses'

// Event source identification
export type EventSourceType = 'agent_log' | 'system_log' | 'orchestrator_chat' | 'thinking_block' | 'tool_use_block'

// Combined log entry for event stream display
export interface EventStreamEntry {
  id: string
  lineNumber: number
  sourceType: EventSourceType  // Identifies which table/component to use
  level: LogLevel | 'SUCCESS'
  agentId?: string
  agentName?: string
  content: string
  tokens?: number
  timestamp: Date | string
  eventType?: string
  eventCategory?: EventCategory
  metadata?: Record<string, any>
}

// Chat message types
export type ChatMessageType = 'text' | 'thinking' | 'tool_use'

// Base chat message
export interface BaseChatMessage {
  id: string
  sender: 'user' | 'orchestrator'
  timestamp: string
  type: ChatMessageType
}

// Text message (standard chat)
export interface TextChatMessage extends BaseChatMessage {
  type: 'text'
  content: string
}

// Thinking message (orchestrator internal thoughts)
export interface ThinkingChatMessage extends BaseChatMessage {
  type: 'thinking'
  thinking: string
}

// Tool use message (orchestrator actions)
export interface ToolUseChatMessage extends BaseChatMessage {
  type: 'tool_use'
  toolName: string
  toolInput: Record<string, any> | null
}

// Union type for all chat messages
export type ChatMessage = TextChatMessage | ThinkingChatMessage | ToolUseChatMessage

// Application stats for header
export interface AppStats {
  active: number
  running: number
  logs: number
  cost: number
}

// WebSocket message types
export interface WSMessage {
  type: 'agent_update' | 'log_entry' | 'chat_message' | 'system_event'
  data: any
}

// ═══════════════════════════════════════════════════════════
// API REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════

// Load chat history
export interface LoadChatRequest {
  orchestrator_agent_id: string
  limit?: number
}

export interface LoadChatResponse {
  status: string
  messages: Array<{
    id: string
    orchestrator_agent_id: string
    sender_type: 'user' | 'orchestrator' | 'agent'
    receiver_type: 'user' | 'orchestrator' | 'agent'
    message: string
    agent_id: string | null
    metadata: Record<string, any>
    created_at: string
    updated_at: string
  }>
  turn_count: number
}

// Send chat message
export interface SendChatRequest {
  message: string
  orchestrator_agent_id: string
}

export interface SendChatResponse {
  status: string
  message: string
}

// WebSocket chat stream message
export interface ChatStreamMessage {
  type: 'chat_stream' | 'chat_typing' | 'error'
  orchestrator_agent_id?: string
  chunk?: string
  is_complete?: boolean
  is_typing?: boolean
  error_message?: string
  details?: any
  timestamp?: string
}

// ═══════════════════════════════════════════════════════════
// EVENT ROW COMPONENT PROPS
// ═══════════════════════════════════════════════════════════

// Props for AgentLogRow component
export interface AgentLogRowProps {
  event: AgentLog
  lineNumber: number
}

// Props for SystemLogRow component
export interface SystemLogRowProps {
  event: SystemLog
  lineNumber: number
}

// Props for OrchestratorChatRow component
export interface OrchestratorChatRowProps {
  event: OrchestratorChat
  lineNumber: number
}

// ═══════════════════════════════════════════════════════════
// AUTOCOMPLETE TYPES
// ═══════════════════════════════════════════════════════════

export type CompletionType = 'none' | 'autocomplete'

export interface AutocompleteItem {
  completion: string
  reasoning: string
}

export interface AutocompleteResponse {
  status: string
  autocompletes: AutocompleteItem[]
  total_items: number
  orchestrator_agent_id: string
  timestamp: string
}

export interface AutocompleteGenerateRequest {
  user_input: string
  orchestrator_agent_id: string
}

export interface AutocompleteUpdateRequest {
  orchestrator_agent_id: string
  completion_type: CompletionType
  user_input_on_enter?: string
  user_input_before_completion?: string
  autocomplete_item?: string
  reasoning?: string
}

// ═══════════════════════════════════════════════════════════
// AI DEVELOPER WORKFLOW (ADW) TYPES
// ═══════════════════════════════════════════════════════════

export type AdwStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled'

export interface AiDeveloperWorkflow {
  id: string
  orchestrator_agent_id: string | null
  adw_name: string
  workflow_type: string
  description: string | null
  status: AdwStatus
  current_step: string | null
  total_steps: number
  completed_steps: number
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  input_data: Record<string, any>
  output_data: Record<string, any>
  error_message: string | null
  error_step: string | null
  error_count: number
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

// ADW Event (from agent_logs for swimlane squares)
export interface AdwEvent {
  id: string
  agent_id: string | null
  adw_id: string
  adw_step: string | null
  event_category: EventCategory
  event_type: string
  summary: string | null
  payload: Record<string, any> | null
  timestamp: string
}

// ADW Step Summary (for swimlane lanes)
export interface AdwStepSummary {
  step: string
  event_count: number
  event_types: Record<string, number>
  agent_id: string | null
  started_at: string | null
  ended_at: string | null
}

// View mode for center column
export type ViewMode = 'logs' | 'adws'

// ADW API Response Types
export interface ListAdwsResponse {
  status: string
  adws: AiDeveloperWorkflow[]
  count: number
}

export interface GetAdwResponse {
  status: string
  adw: AiDeveloperWorkflow
}

export interface GetAdwEventsResponse {
  status: string
  adw_id: string
  events: AdwEvent[]
  events_by_step: Record<string, AdwEvent[]>
  count: number
}

export interface GetAdwSummaryResponse {
  status: string
  adw: AiDeveloperWorkflow
  steps: AdwStepSummary[]
  total_events: number
}
