/**
 * Orchestrator Store
 *
 * Main Pinia store for managing application state with real API integration.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Agent,
  AgentLog,
  SystemLog,
  OrchestratorChat,
  OrchestratorAgent,
  EventStreamEntry,
  EventSourceType,
  EventCategory,
  LogLevel,
  ChatMessage,
  AppStats,
  EventStreamFilter,
  AutocompleteItem,
  CompletionType,
  // ADW Types
  AiDeveloperWorkflow,
  AdwEvent,
  AdwStepSummary,
  ViewMode
} from '../types'
import * as chatService from '../services/chatService'
import * as agentService from '../services/agentService'
import { getEvents } from '../services/eventService'
import * as autocompleteService from '../services/autocompleteService'
import * as adwService from '../services/adwService'
import { DEFAULT_EVENT_HISTORY_LIMIT } from '../config/constants'
import { useAgentPulse } from '../composables/useAgentPulse'

// Default orchestrator agent ID (will be loaded from backend on init)
const DEFAULT_ORCHESTRATOR_ID = 'default-orchestrator'

// Initialize pulse composable at module level
const agentPulse = useAgentPulse()

export const useOrchestratorStore = defineStore('orchestrator', () => {
  // ═══════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════

  // Agents
  const agents = ref<Agent[]>([])
  const selectedAgentId = ref<string | null>(null)

  // Orchestrator
  const orchestratorAgentId = ref<string>(DEFAULT_ORCHESTRATOR_ID)
  const orchestratorAgent = ref<OrchestratorAgent | null>(null)

  // Event Stream
  const eventStreamEntries = ref<EventStreamEntry[]>([])
  const eventStreamFilter = ref<EventStreamFilter>('all')
  const autoScroll = ref<boolean>(true)

  // File Tracking - maps parent_log_id → file tracking data
  const fileTrackingEvents = ref<Map<string, any>>(new Map())

  // Chat
  const chatMessages = ref<ChatMessage[]>([])
  const isTyping = ref(false)

  // Command Input
  const commandInputVisible = ref<boolean>(false)

  // Chat Width
  const chatWidth = ref<'sm' | 'md' | 'lg'>('sm')

  // Autocomplete
  const autocompleteItems = ref<AutocompleteItem[]>([])
  const autocompleteLoading = ref<boolean>(false)
  const autocompleteError = ref<string | null>(null)

  // WebSocket
  const isConnected = ref(false)
  let wsConnection: WebSocket | null = null

  // WebSocket session event counter
  const websocketEventCount = ref<number>(0)

  // Autocomplete loading timeout (safety feature to prevent stuck spinner)
  let autocompleteLoadingTimeout: NodeJS.Timeout | null = null
  const AUTOCOMPLETE_TIMEOUT_MS = 10000 // 10 seconds

  // ═══════════════════════════════════════════════════════════
  // ADW (AI Developer Workflow) STATE
  // ═══════════════════════════════════════════════════════════

  // View mode toggle (logs vs ADW swimlanes)
  const viewMode = ref<ViewMode>('logs')

  // ADW list
  const adws = ref<AiDeveloperWorkflow[]>([])
  const selectedAdwId = ref<string | null>(null)

  // ADW events for selected ADW (swimlane squares)
  const adwEvents = ref<AdwEvent[]>([])
  const adwEventsByStep = ref<Record<string, AdwEvent[]>>({})

  // ADW events map for all ADWs (keyed by adw_id)
  const allAdwEvents = ref<Record<string, AdwEvent[]>>({})
  const allAdwEventsByStep = ref<Record<string, Record<string, AdwEvent[]>>>({})

  // ADW loading states
  const adwsLoading = ref<boolean>(false)
  const adwEventsLoading = ref<boolean>(false)

  // ═══════════════════════════════════════════════════════════
  // GETTERS
  // ═══════════════════════════════════════════════════════════

  // Filter agents by status
  const activeAgents = computed(() =>
    agents.value.filter(a => !a.archived && a.status !== 'complete')
  )

  const runningAgents = computed(() =>
    agents.value.filter(a => a.status === 'executing')
  )

  const idleAgents = computed(() =>
    agents.value.filter(a => a.status === 'idle')
  )

  // Get selected agent
  const selectedAgent = computed(() =>
    selectedAgentId.value
      ? agents.value.find(a => a.id === selectedAgentId.value)
      : null
  )

  // Filter event stream based on current filter
  const filteredEventStream = computed(() => {
    switch (eventStreamFilter.value) {
      case 'errors':
        return eventStreamEntries.value.filter(e => e.level === 'ERROR')
      case 'hooks':
        return eventStreamEntries.value.filter(e => e.eventCategory === 'hook')
      case 'responses':
        return eventStreamEntries.value.filter(e => e.eventCategory === 'response')
      default:
        return eventStreamEntries.value
    }
  })

  // Application stats
  const stats = computed<AppStats>(() => ({
    active: activeAgents.value.length,
    running: runningAgents.value.length,
    logs: eventStreamEntries.value.length,
    cost: agents.value.reduce((sum, agent) => sum + agent.total_cost, 0)
  }))

  // Chat width in pixels
  const chatWidthPixels = computed(() => {
    const widths = {
      sm: 418,
      md: 518,
      lg: 618
    }
    return widths[chatWidth.value]
  })

  // Autocomplete computed
  const hasAutocompleteItems = computed(() => autocompleteItems.value.length > 0)

  // ═══════════════════════════════════════════════════════════
  // ADW GETTERS
  // ═══════════════════════════════════════════════════════════

  // Selected ADW record
  const selectedAdw = computed(() =>
    selectedAdwId.value
      ? adws.value.find(a => a.id === selectedAdwId.value)
      : null
  )

  // ADWs by status
  const runningAdws = computed(() =>
    adws.value.filter(a => a.status === 'in_progress')
  )

  const completedAdws = computed(() =>
    adws.value.filter(a => a.status === 'completed')
  )

  const failedAdws = computed(() =>
    adws.value.filter(a => a.status === 'failed')
  )

  // ADW steps from events (for swimlane lanes)
  const adwSteps = computed(() => Object.keys(adwEventsByStep.value))

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - CHAT
  // ═══════════════════════════════════════════════════════════

  async function loadChatHistory() {
    try {
      console.log('Loading chat history...')
      const response = await chatService.loadChatHistory(orchestratorAgentId.value)

      // Convert backend messages to frontend ChatMessage format
      chatMessages.value = response.messages.map(msg => {
        const sender = msg.sender_type === 'user' ? 'user' : 'orchestrator'

        // Check metadata to determine message type
        const metadataType = msg.metadata?.type

        if (metadataType === 'thinking') {
          // Thinking block
          return {
            id: msg.id,
            sender,
            type: 'thinking' as const,
            thinking: msg.metadata.thinking,
            timestamp: msg.created_at
          }
        } else if (metadataType === 'tool_use') {
          // Tool use block
          return {
            id: msg.id,
            sender,
            type: 'tool_use' as const,
            toolName: msg.metadata.tool_name,
            toolInput: msg.metadata.tool_input,
            timestamp: msg.created_at
          }
        } else {
          // Regular text message
          return {
            id: msg.id,
            sender,
            type: 'text' as const,
            content: msg.message,
            timestamp: msg.created_at
          }
        }
      })

      console.log(`Loaded ${chatMessages.value.length} messages (${response.turn_count} turns)`)
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }

  function addChatMessage(message: ChatMessage) {
    chatMessages.value.push(message)
  }

  async function sendUserMessage(content: string) {
    // Add user message immediately to UI
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      sender: 'user',
      type: 'text',
      content,
      timestamp: new Date().toISOString()
    }
    addChatMessage(userMessage)

    try {
      // Send to backend (response will come via WebSocket streaming)
      await chatService.sendMessage(content, orchestratorAgentId.value)
      console.log('Message sent to backend')
    } catch (error) {
      console.error('Failed to send message:', error)
      // Show error to user
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        sender: 'orchestrator',
        type: 'text',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date().toISOString()
      }
      addChatMessage(errorMessage)
    }
  }

  function clearChat() {
    chatMessages.value = []
  }

  function toggleChatWidth() {
    const sizes = ['sm', 'md', 'lg'] as const
    const currentIndex = sizes.indexOf(chatWidth.value)
    const nextIndex = (currentIndex + 1) % sizes.length
    chatWidth.value = sizes[nextIndex]

    // Persist to localStorage
    try {
      localStorage.setItem('orchestrator_chat_width', chatWidth.value)
    } catch (error) {
      console.warn('Failed to save chat width preference:', error)
    }
  }

  function initializeChatWidth() {
    try {
      const saved = localStorage.getItem('orchestrator_chat_width')
      if (saved && ['sm', 'md', 'lg'].includes(saved)) {
        chatWidth.value = saved as 'sm' | 'md' | 'lg'
      }
    } catch (error) {
      console.warn('Failed to load chat width preference:', error)
      // Fall back to default 'sm'
    }
  }

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - AUTOCOMPLETE
  // ═══════════════════════════════════════════════════════════

  async function generateAutocomplete(userInput: string) {
    try {
      autocompleteLoading.value = true
      autocompleteError.value = null

      const response = await autocompleteService.generateAutocomplete(
        userInput,
        orchestratorAgentId.value
      )

      autocompleteItems.value = response.autocompletes
      console.log(`Generated ${response.autocompletes.length} autocomplete suggestions`)
    } catch (error) {
      console.error('Failed to generate autocomplete:', error)
      autocompleteError.value = error instanceof Error ? error.message : 'Unknown error'
      autocompleteItems.value = []
    } finally {
      autocompleteLoading.value = false
    }
  }

  async function updateAutocompleteHistory(
    completion_type: CompletionType,
    user_input_on_enter?: string,
    user_input_before_completion?: string,
    autocomplete_item?: string,
    reasoning?: string
  ) {
    try {
      await autocompleteService.updateAutocompleteHistory({
        orchestrator_agent_id: orchestratorAgentId.value,
        completion_type,
        user_input_on_enter,
        user_input_before_completion,
        autocomplete_item,
        reasoning
      })
      console.log('Autocomplete history updated:', completion_type)
    } catch (error) {
      console.error('Failed to update autocomplete history:', error)
    }
  }

  function clearAutocomplete() {
    autocompleteItems.value = []
    autocompleteError.value = null
  }

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - ADW (AI Developer Workflow)
  // ═══════════════════════════════════════════════════════════

  /**
   * Set the view mode (logs or ADW swimlanes)
   */
  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
    console.log(`View mode changed to: ${mode}`)

    // If switching to ADW view and no ADWs loaded, fetch them
    if (mode === 'adws' && adws.value.length === 0) {
      fetchAdws()
    }
  }

  /**
   * Toggle between logs and adws view modes
   */
  function toggleViewMode() {
    const newMode = viewMode.value === 'logs' ? 'adws' : 'logs'
    setViewMode(newMode)
  }

  /**
   * Fetch all ADWs for the current orchestrator
   */
  async function fetchAdws(status?: string) {
    try {
      adwsLoading.value = true
      console.log('Fetching ADWs...')

      const response = await adwService.listAdws(
        orchestratorAgentId.value,
        status,
        50
      )

      adws.value = response.adws
      console.log(`Loaded ${response.count} ADWs`)

      // Fetch events for all ADWs (for inline swimlane squares)
      await fetchAllAdwEvents()
    } catch (error) {
      console.error('Failed to fetch ADWs:', error)
    } finally {
      adwsLoading.value = false
    }
  }

  /**
   * Fetch events for all ADWs (for inline swimlane display)
   */
  async function fetchAllAdwEvents() {
    const eventPromises = adws.value.map(async (adw) => {
      try {
        const response = await adwService.getAdwEvents(adw.id, 2000, undefined, true)
        return { adwId: adw.id, events: response.events, eventsByStep: response.events_by_step }
      } catch (error) {
        console.error(`Failed to fetch events for ADW ${adw.id}:`, error)
        return { adwId: adw.id, events: [], eventsByStep: {} }
      }
    })

    const results = await Promise.all(eventPromises)

    // Build the allAdwEvents and allAdwEventsByStep maps
    const eventsMap: Record<string, AdwEvent[]> = {}
    const eventsByStepMap: Record<string, Record<string, AdwEvent[]>> = {}
    results.forEach(({ adwId, events, eventsByStep }) => {
      eventsMap[adwId] = events
      eventsByStepMap[adwId] = eventsByStep
    })
    allAdwEvents.value = eventsMap
    allAdwEventsByStep.value = eventsByStepMap
    console.log(`Loaded events for ${results.length} ADWs`)
  }

  /**
   * Select an ADW and load its events
   */
  async function selectAdw(adwId: string | null) {
    selectedAdwId.value = adwId

    if (adwId) {
      await fetchAdwEvents(adwId)
    } else {
      adwEvents.value = []
      adwEventsByStep.value = {}
    }
  }

  /**
   * Fetch events for a specific ADW (swimlane squares)
   */
  async function fetchAdwEvents(adwId: string) {
    try {
      adwEventsLoading.value = true
      console.log(`Fetching events for ADW: ${adwId}`)

      const response = await adwService.getAdwEvents(adwId, 2000, undefined, true)

      adwEvents.value = response.events
      adwEventsByStep.value = response.events_by_step
      console.log(`Loaded ${response.count} events across ${Object.keys(response.events_by_step).length} steps`)
    } catch (error) {
      console.error(`Failed to fetch ADW events for ${adwId}:`, error)
    } finally {
      adwEventsLoading.value = false
    }
  }

  /**
   * Handle ADW created WebSocket event
   */
  function handleAdwCreated(message: any) {
    console.log('ADW created:', message)
    const adw = message.adw
    if (adw) {
      // Add to front of list (newest first)
      adws.value = [adw, ...adws.value]
    }
  }

  /**
   * Handle ADW updated WebSocket event
   */
  function handleAdwUpdated(message: any) {
    console.log('ADW updated:', message)
    const adwId = message.adw_id
    const adwData = message.adw

    if (adwId && adwData) {
      const index = adws.value.findIndex(a => a.id === adwId)
      if (index !== -1) {
        adws.value[index] = { ...adws.value[index], ...adwData }
        // Force reactivity
        adws.value = [...adws.value]
      }
    }
  }

  /**
   * Handle ADW event WebSocket (new swimlane square)
   */
  function handleAdwEvent(message: any) {
    console.log('ADW event:', message)
    const adwId = message.adw_id
    const event = message.event

    if (!event || !adwId) return

    // Trigger pulse for the agent associated with this event
    if (event.agent_id) {
      const eventType = event.event_type?.toLowerCase() || ''
      const isRelevantEvent =
        eventType.includes('tool') ||
        eventType.includes('hook') ||
        event.event_category === 'hook' ||
        eventType.includes('thinking') ||
        eventType.includes('text')

      if (isRelevantEvent) {
        agentPulse.triggerPulse(event.agent_id)
        console.log(`✨ Pulsing ADW agent ${event.agent_id} for event: ${event.event_type}`)
      }
    }

    // Also add the ADW event to the event stream (logs view)
    const lineNumber = eventStreamEntries.value.length + 1
    const agentName = event.adw_step || `ADW:${adwId.slice(0, 8)}`

    // Create a properly formatted originalEvent for AgentLogRow (uses snake_case)
    const formattedOriginalEvent = {
      ...event,
      agent_name: agentName,  // AgentLogRow expects snake_case
      agent_id: event.agent_id || '',
      event_type: event.event_type,
      event_category: event.event_category || 'hook',
      content: event.content || '',
      summary: event.summary || event.event_type,
      payload: event.payload || {},
      timestamp: event.timestamp || new Date().toISOString(),
    }

    const logEntry: EventStreamEntry = {
      id: event.id || crypto.randomUUID(),
      lineNumber,
      sourceType: 'agent_log',
      level: mapEventCategoryToLevel(event.event_category || 'hook', event.event_type || ''),
      agentId: event.agent_id,
      agentName: agentName,
      content: event.summary || event.content || event.event_type,
      tokens: extractTokensFromPayload(event.payload || {}),
      timestamp: new Date(event.timestamp || Date.now()),
      eventType: event.event_type,
      eventCategory: event.event_category || 'hook',
      metadata: {
        ...event.payload,
        adw_id: adwId,
        adw_step: event.adw_step,
        originalEvent: formattedOriginalEvent
      }
    }

    // Force Vue reactivity by replacing the array
    eventStreamEntries.value = [...eventStreamEntries.value, logEntry]
    console.log(`Added ADW event to event stream: ${event.event_type}`)

    // Always update allAdwEvents (for inline swimlane display on all cards)
    if (!allAdwEvents.value[adwId]) {
      allAdwEvents.value[adwId] = []
    }
    allAdwEvents.value[adwId] = [...allAdwEvents.value[adwId], event]
    // Force reactivity
    allAdwEvents.value = { ...allAdwEvents.value }

    // Update allAdwEventsByStep
    const step = event.adw_step || '_workflow'
    if (!allAdwEventsByStep.value[adwId]) {
      allAdwEventsByStep.value[adwId] = {}
    }
    if (!allAdwEventsByStep.value[adwId][step]) {
      allAdwEventsByStep.value[adwId][step] = []
    }
    allAdwEventsByStep.value[adwId][step] = [...allAdwEventsByStep.value[adwId][step], event]
    // Force reactivity
    allAdwEventsByStep.value = { ...allAdwEventsByStep.value }

    // Also update selected ADW events if viewing this ADW
    if (adwId === selectedAdwId.value) {
      adwEvents.value = [...adwEvents.value, event]

      if (!adwEventsByStep.value[step]) {
        adwEventsByStep.value[step] = []
      }
      adwEventsByStep.value[step] = [...adwEventsByStep.value[step], event]
      // Force reactivity
      adwEventsByStep.value = { ...adwEventsByStep.value }
    }
  }

  /**
   * Handle ADW step change WebSocket event
   */
  function handleAdwStepChange(message: any) {
    console.log('ADW step change:', message)
    // Update the ADW's current step if we have it
    const adwId = message.adw_id
    const step = message.step

    if (adwId) {
      const index = adws.value.findIndex(a => a.id === adwId)
      if (index !== -1) {
        adws.value[index].current_step = step
        adws.value = [...adws.value]
      }
    }
  }

  /**
   * Handle ADW event summary update WebSocket event
   * Updates an existing event's summary when AI summary is generated
   */
  function handleAdwEventSummaryUpdate(message: any) {
    console.log('ADW event summary update:', message)
    const adwId = message.adw_id
    const eventId = message.event_id
    const summary = message.summary

    if (!adwId || !eventId || !summary) return

    // Update in allAdwEvents
    if (allAdwEvents.value[adwId]) {
      const eventIndex = allAdwEvents.value[adwId].findIndex((e: any) => e.id === eventId)
      if (eventIndex !== -1) {
        allAdwEvents.value[adwId][eventIndex].summary = summary
        allAdwEvents.value = { ...allAdwEvents.value }
      }
    }

    // Update in allAdwEventsByStep
    if (allAdwEventsByStep.value[adwId]) {
      for (const step in allAdwEventsByStep.value[adwId]) {
        const events = allAdwEventsByStep.value[adwId][step]
        const eventIndex = events.findIndex((e: any) => e.id === eventId)
        if (eventIndex !== -1) {
          events[eventIndex].summary = summary
          allAdwEventsByStep.value = { ...allAdwEventsByStep.value }
          break
        }
      }
    }

    // Update in selected ADW events if viewing this ADW
    if (adwId === selectedAdwId.value) {
      const eventIndex = adwEvents.value.findIndex((e: any) => e.id === eventId)
      if (eventIndex !== -1) {
        adwEvents.value[eventIndex].summary = summary
        adwEvents.value = [...adwEvents.value]
      }

      // Also update in adwEventsByStep
      for (const step in adwEventsByStep.value) {
        const events = adwEventsByStep.value[step]
        const idx = events.findIndex((e: any) => e.id === eventId)
        if (idx !== -1) {
          events[idx].summary = summary
          adwEventsByStep.value = { ...adwEventsByStep.value }
          break
        }
      }
    }

    // Update in eventStreamEntries (logs view)
    const streamIndex = eventStreamEntries.value.findIndex(e => e.id === eventId)
    if (streamIndex !== -1) {
      eventStreamEntries.value[streamIndex].content = summary
      if (eventStreamEntries.value[streamIndex].metadata?.originalEvent) {
        eventStreamEntries.value[streamIndex].metadata.originalEvent.summary = summary
      }
      eventStreamEntries.value = [...eventStreamEntries.value]
    }

    console.log(`✨ Updated summary for event ${eventId}: ${summary}`)
  }

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - WEBSOCKET
  // ═══════════════════════════════════════════════════════════

  function incrementWebSocketEventCount() {
    websocketEventCount.value += 1
  }

  function connectWebSocket() {
    // Clean up any existing connection first
    if (wsConnection) {
      if (wsConnection.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected')
        return
      }
      // Clean up dead connection
      wsConnection.close()
      wsConnection = null
    }

    const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || 'ws://127.0.0.1:9403/ws'
    console.log('Connecting to WebSocket:', wsUrl)

    try {
      wsConnection = chatService.connectWebSocket(wsUrl, {
        onMessageReceived: () => {
          incrementWebSocketEventCount()
        },
        onChatStream: handleChatStream,
        onTyping: handleTyping,
        onAgentLog: (message) => {
          if (message.log) {
            addAgentLogEvent(message.log)
          }
        },
        onOrchestratorChat: (message) => {
          console.log('[WebSocket] orchestrator_chat event received:', message)
          console.log('[WebSocket] message.message exists?', !!message.message)
          console.log('[WebSocket] Full message structure:', JSON.stringify(message, null, 2))
          // Backend sends the chat data in 'message' field, not 'chat'
          if (message.message) {
            console.log('[WebSocket] Calling addOrchestratorChatEvent with:', message.message)
            addOrchestratorChatEvent(message.message)
          } else {
            console.error('[WebSocket] ❌ No message.message field found in:', message)
          }
        },
        onThinkingBlock: (message) => {
          if (message.data) {
            addThinkingBlockEvent(message.data)
            // Also add to chat messages
            addThinkingToChatMessage(message.data)
          }
        },
        onToolUseBlock: (message) => {
          console.log('[ToolUseBlock] Received WebSocket event:', message)
          if (message.data) {
            console.log('[ToolUseBlock] Processing data:', message.data)
            addToolUseBlockEvent(message.data)
            // Also add to chat messages
            addToolUseToChatMessage(message.data)
          } else {
            console.warn('[ToolUseBlock] No data in message:', message)
          }
        },
        onAgentCreated: handleAgentCreated,
        onAgentUpdated: handleAgentUpdated,
        onAgentDeleted: handleAgentDeleted,
        onAgentStatusChange: handleAgentStatusChange,
        onAgentSummaryUpdate: handleAgentSummaryUpdate,
        onOrchestratorUpdated: handleOrchestratorUpdated,
        onAutocompleteStarted: handleAutocompleteStarted,
        onAutocompleteCompleted: handleAutocompleteCompleted,
        // ADW handlers
        onAdwCreated: handleAdwCreated,
        onAdwUpdated: handleAdwUpdated,
        onAdwEvent: handleAdwEvent,
        onAdwStepChange: handleAdwStepChange,
        onAdwEventSummaryUpdate: handleAdwEventSummaryUpdate,
        onError: handleWebSocketError,
        onConnected: () => {
          isConnected.value = true
          websocketEventCount.value = 0  // Reset counter for new session
          console.log('WebSocket connected - event counter reset')
        },
        onDisconnected: () => {
          isConnected.value = false
          console.log('WebSocket disconnected')
        }
      })
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }

  function disconnectWebSocket() {
    if (wsConnection) {
      chatService.disconnect(wsConnection)
      wsConnection = null
      isConnected.value = false
    }

    // Reset counter on disconnect
    websocketEventCount.value = 0

    // CRITICAL: Cleanup pulse animations to prevent memory leaks
    agentPulse.clearAllPulses()

    // CRITICAL: Cleanup autocomplete loading timeout to prevent memory leaks
    if (autocompleteLoadingTimeout) {
      clearTimeout(autocompleteLoadingTimeout)
      autocompleteLoadingTimeout = null
    }
  }

  function handleChatStream(chunk: string, isComplete: boolean) {
    if (!isComplete) {
      // Show typing indicator while streaming
      // Don't accumulate or display chunks - the complete message will come via orchestrator_chat event
      isTyping.value = true
    } else {
      // Streaming complete - stop showing typing indicator
      // The real message with database ID will come via orchestrator_chat WebSocket event
      isTyping.value = false
    }
  }

  function handleTyping(typing: boolean) {
    isTyping.value = typing
  }

  function handleWebSocketError(error: any) {
    console.error('WebSocket error:', error)
    isTyping.value = false
  }

  function handleWebSocketMessage(message: any) {
    console.log('WebSocket message received:', message)
    // Additional message handling if needed
  }

  function handleAgentLog(message: any) {
    console.log('Agent log received:', message)

    // Look up agent name from agents array
    const agent = agents.value.find(a => a.id === message.agent_id)
    const agentName = agent?.name || message.agent_id

    // Map agent_log to EventStreamEntry format
    const entry: EventStreamEntry = {
      id: crypto.randomUUID(),
      lineNumber: eventStreamEntries.value.length + 1,
      timestamp: message.timestamp || new Date().toISOString(),
      level: message.event_type?.includes('Error') ? 'ERROR' : 'INFO',
      agentId: message.agent_id,
      agentName: agentName, // Actual agent name for filtering
      content: message.payload?.summary || message.event_type || 'Agent event',
      eventCategory: message.event_category,
      eventType: message.event_type
    }

    addEventStreamEntry(entry)
  }

  function handleAgentCreated(message: any) {
    console.log('Agent created:', message)

    // Add new agent to array or reload all agents
    loadAgents().catch(err => console.error('Failed to reload agents after creation:', err))
  }

  function handleAgentUpdated(message: any) {
    console.log('Agent updated:', message)

    // Update agent with all provided fields (tokens, cost, status, etc.)
    const agentId = message.agent_id
    const agentData = message.agent

    if (agentId && agentData) {
      const index = agents.value.findIndex(a => a.id === agentId)
      if (index !== -1) {
        // Merge updated fields into existing agent
        // Only update fields that are provided in agentData
        agents.value[index] = {
          ...agents.value[index],
          ...agentData
        }
        console.log(`Updated agent ${agentId}:`, agentData)
      }
    }
  }

  function handleAgentDeleted(message: any) {
    console.log('Agent deleted:', message)

    // Remove agent from array
    const agentId = message.agent_id

    if (agentId) {
      const index = agents.value.findIndex(a => a.id === agentId)
      if (index !== -1) {
        // Use spread operator to trigger Vue reactivity
        agents.value = agents.value.filter(a => a.id !== agentId)
        console.log(`Removed agent ${agentId} from list`)
      }
    }
  }

  function handleAgentStatusChange(message: any) {
    console.log('Agent status changed:', message)

    // Update specific agent status in array
    const agentId = message.agent_id
    const newStatus = message.new_status

    if (agentId && newStatus) {
      const index = agents.value.findIndex(a => a.id === agentId)
      if (index !== -1) {
        agents.value[index].status = newStatus
      }
    }
  }

  function handleAgentSummaryUpdate(message: any) {
    console.log('Agent summary update:', message)

    // Update specific agent's latest summary
    const agentId = message.agent_id
    const summary = message.summary

    if (agentId && summary) {
      const index = agents.value.findIndex(a => a.id === agentId)
      if (index !== -1) {
        agents.value[index].latest_summary = summary
        console.log(`Updated summary for agent ${agentId}: ${summary}`)
      }
    }
  }

  function handleOrchestratorUpdated(message: any) {
    console.log('Orchestrator updated:', message)

    // Update orchestrator agent data with live cost and token updates
    const orchestratorData = message.orchestrator

    if (orchestratorData && orchestratorAgent.value) {
      // Update orchestratorAgent with new cost and token data
      orchestratorAgent.value = {
        ...orchestratorAgent.value,
        input_tokens: orchestratorData.input_tokens ?? orchestratorAgent.value.input_tokens,
        output_tokens: orchestratorData.output_tokens ?? orchestratorAgent.value.output_tokens,
        total_cost: orchestratorData.total_cost ?? orchestratorAgent.value.total_cost,
        updated_at: orchestratorData.updated_at ?? orchestratorAgent.value.updated_at
      }

      console.log(`✅ Updated orchestrator cost: $${orchestratorData.total_cost?.toFixed(4)} | Tokens: ${orchestratorData.input_tokens + orchestratorData.output_tokens}`)
    }
  }

  function handleAutocompleteStarted(message: any) {
    console.log('[Autocomplete] Started:', message)
    autocompleteLoading.value = true
    console.log('🔄 Autocomplete loading started via WebSocket')

    // Safety timeout: clear loading after 10 seconds max to prevent stuck spinner
    if (autocompleteLoadingTimeout) {
      clearTimeout(autocompleteLoadingTimeout)
    }
    autocompleteLoadingTimeout = setTimeout(() => {
      if (autocompleteLoading.value) {
        console.warn('⚠️ [Autocomplete] Timeout: Force clearing loading state after 10 seconds')
        autocompleteLoading.value = false
        autocompleteLoadingTimeout = null
      }
    }, AUTOCOMPLETE_TIMEOUT_MS)
  }

  function handleAutocompleteCompleted(message: any) {
    console.log('[Autocomplete] Completed:', message)

    // Clear the safety timeout
    if (autocompleteLoadingTimeout) {
      clearTimeout(autocompleteLoadingTimeout)
      autocompleteLoadingTimeout = null
    }

    autocompleteLoading.value = false
    console.log('✅ Autocomplete loading completed via WebSocket')
  }

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - AGENTS
  // ═══════════════════════════════════════════════════════════

  function selectAgent(id: string) {
    selectedAgentId.value = id
  }

  function clearAgentSelection() {
    selectedAgentId.value = null
  }

  async function loadAgents() {
    try {
      console.log('Loading agents...')
      const loadedAgents = await agentService.loadAgents()
      agents.value = loadedAgents
      console.log(`Loaded ${agents.value.length} agents`)
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  function addAgent(agent: Agent) {
    agents.value.push(agent)
  }

  function updateAgent(id: string, updates: Partial<Agent>) {
    const index = agents.value.findIndex(a => a.id === id)
    if (index !== -1) {
      agents.value[index] = { ...agents.value[index], ...updates }
    }
  }

  function removeAgent(id: string) {
    const index = agents.value.findIndex(a => a.id === id)
    if (index !== -1) {
      agents.value.splice(index, 1)
    }
  }

  // ═══════════════════════════════════════════════════════════
  // ACTIONS - EVENT STREAM
  // ═══════════════════════════════════════════════════════════

  function addEventStreamEntry(entry: EventStreamEntry) {
    // Force Vue reactivity by replacing the array instead of mutating
    eventStreamEntries.value = [...eventStreamEntries.value, entry]
  }

  function clearEventStream() {
    eventStreamEntries.value = []
  }

  function setEventStreamFilter(filter: EventStreamFilter) {
    eventStreamFilter.value = filter
  }

  function toggleAutoScroll() {
    autoScroll.value = !autoScroll.value
  }

  function toggleCommandInput() {
    commandInputVisible.value = !commandInputVisible.value
  }

  function showCommandInput() {
    commandInputVisible.value = true
  }

  function hideCommandInput() {
    commandInputVisible.value = false
  }

  function exportEventStream() {
    const data = JSON.stringify(filteredEventStream.value, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `event-stream-${new Date().toISOString()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ═══════════════════════════════════════════════════════════
  // EVENT STREAM ACTIONS
  // ═══════════════════════════════════════════════════════════

  /**
   * Fetch event history from backend
   */
  async function fetchEventHistory(params: {
    agent_id?: string
    task_slug?: string
    event_types?: string
    limit?: number
    offset?: number
  } = {}) {
    try {
      const response = await getEvents(params)

      // Convert mixed events to EventStreamEntry format
      const entries: EventStreamEntry[] = response.events.map((event: any, index) => {
        const baseEntry = {
          id: event.id,
          lineNumber: (params.offset || 0) + index + 1,
          sourceType: event.sourceType as EventSourceType,
          timestamp: new Date(event.timestamp || event.created_at)
        }

        // Handle different event types
        switch (event.sourceType) {
          case 'agent_log':
            // Look up agent name from agents array or use event.agent_name if provided
            const agent = agents.value.find(a => a.id === event.agent_id)
            const agentName = event.agent_name || agent?.name || event.agent_id

            return {
              ...baseEntry,
              level: mapEventCategoryToLevel(event.event_category, event.event_type),
              agentId: event.agent_id,
              agentName: agentName, // Actual agent name for filtering
              content: event.summary || event.content || event.event_type,
              tokens: extractTokensFromPayload(event.payload),
              eventType: event.event_type,
              eventCategory: event.event_category,
              metadata: { ...event.payload, originalEvent: event }
            } as EventStreamEntry

          case 'orchestrator_chat':
            return {
              ...baseEntry,
              level: 'INFO' as LogLevel,
              content: event.message,
              metadata: {
                sender_type: event.sender_type,
                receiver_type: event.receiver_type,
                agent_id: event.agent_id,
                ...event.metadata,
                originalEvent: event
              }
            } as EventStreamEntry

          default:
            return baseEntry as EventStreamEntry
        }
      })

      // Replace or append based on offset
      if (params.offset === 0 || !params.offset) {
        eventStreamEntries.value = entries
      } else {
        eventStreamEntries.value.push(...entries)
      }

      console.log(`Loaded ${entries.length} event history entries`)
    } catch (error) {
      console.error('Failed to fetch event history:', error)
      throw error
    }
  }

  /**
   * Add agent log event from WebSocket
   */
  function addAgentLogEvent(log: any) {
    // Handle FileTrackingBlock events separately
    if (log.event_type === 'FileTrackingBlock') {
      // Store file tracking data mapped to parent log ID
      if (log.parent_log_id) {
        fileTrackingEvents.value.set(log.parent_log_id, log.payload)
        // CRITICAL: Force Vue reactivity by reassigning the Map
        // Vue 3 doesn't track Map.set() operations, so we need to trigger reactivity manually
        fileTrackingEvents.value = new Map(fileTrackingEvents.value)
        console.log(`📂 Stored file tracking for parent log: ${log.parent_log_id}`)
        console.log(`📂 File changes count: ${log.payload.file_changes?.length || 0}`)
        console.log(`📂 Read files count: ${log.payload.read_files?.length || 0}`)
      } else {
        console.warn('FileTrackingBlock received without parent_log_id:', log)
      }
      return
    }

    // Trigger pulse for this agent on relevant events
    if (log.agent_id) {
      const eventType = log.event_type?.toLowerCase() || ''
      const isRelevantEvent =
        eventType.includes('tool') ||
        eventType.includes('hook') ||
        log.event_category === 'hook'

      if (isRelevantEvent) {
        agentPulse.triggerPulse(log.agent_id)
        console.log(`✨ Pulsing agent ${log.agent_id} for event: ${log.event_type}`)
      }
    }

    // Normal log entry creation
    const lineNumber = eventStreamEntries.value.length + 1

    const entry: EventStreamEntry = {
      id: log.id,
      lineNumber,
      sourceType: 'agent_log',
      level: mapEventCategoryToLevel(log.event_category, log.event_type),
      agentId: log.agent_id,
      agentName: log.agent_name,  // Include agent name from the log
      content: log.summary || log.content || log.event_type,
      tokens: extractTokensFromPayload(log.payload),
      timestamp: new Date(log.timestamp),
      eventType: log.event_type,
      eventCategory: log.event_category,
      metadata: {
        ...log.payload,
        originalEvent: log  // Store the full log for reference
      }
    }

    // Force Vue reactivity by replacing the array instead of mutating
    eventStreamEntries.value = [...eventStreamEntries.value, entry]
    console.log(`Added agent log event: ${log.event_type}`)
  }


  /**
   * Add orchestrator chat event from WebSocket
   */
  function addOrchestratorChatEvent(chat: any) {
    const lineNumber = eventStreamEntries.value.length + 1

    // Handle both database format (id, created_at) and WebSocket format (timestamp)
    const entry: EventStreamEntry = {
      id: chat.id || crypto.randomUUID(),
      lineNumber,
      sourceType: 'orchestrator_chat',
      level: 'INFO',
      content: chat.message,
      timestamp: chat.created_at ? new Date(chat.created_at) : chat.timestamp ? new Date(chat.timestamp) : new Date(),
      metadata: {
        sender_type: chat.sender_type,
        receiver_type: chat.receiver_type,
        agent_id: chat.agent_id,
        orchestrator_agent_id: chat.orchestrator_agent_id,
        ...chat.metadata
      }
    }

    // Force Vue reactivity by replacing the array instead of mutating
    eventStreamEntries.value = [...eventStreamEntries.value, entry]
    console.log(`Added orchestrator chat event: ${chat.sender_type} → ${chat.receiver_type}`)

    // Also add to chatMessages array so chat UI gets messages
    const messageId = chat.id || crypto.randomUUID()
    const sender = chat.sender_type === 'user' ? 'user' : 'orchestrator'

    console.log(`[OrchestratorChat] Received message - ID: ${messageId}, Sender: ${sender}, Content: ${chat.message?.substring(0, 50)}...`)

    // Only deduplicate USER messages (orchestrator messages are never pre-added)
    if (sender === 'user') {
      // User messages might already exist (frontend pre-adds them, then backend confirms)
      // Check by content+timestamp since frontend uses random UUID
      const messageTimestamp = new Date(chat.created_at || chat.timestamp || new Date()).getTime()
      const existingMessage = chatMessages.value.find(m => {
        const timeDiff = Math.abs(new Date(m.timestamp).getTime() - messageTimestamp)
        return m.sender === 'user' &&
          m.content === chat.message &&
          timeDiff < 5000 // Within 5 seconds
      })

      if (existingMessage) {
        console.log(`[OrchestratorChat] ❌ SKIPPED duplicate user message`)
        return // Skip duplicate user message
      }
    }

    // Add message to chat UI
    const chatMessage: ChatMessage = {
      id: messageId,
      sender,
      type: 'text',
      content: chat.message,
      timestamp: chat.created_at || chat.timestamp || new Date().toISOString()
    }

    // Force Vue reactivity by replacing the array instead of mutating
    chatMessages.value = [...chatMessages.value, chatMessage]
    console.log(`[OrchestratorChat] ✅ ADDED to chat UI (${chatMessages.value.length} total): ${sender} - ${chat.message?.substring(0, 50)}...`)
  }

  /**
   * Add thinking block event from WebSocket
   */
  function addThinkingBlockEvent(data: any) {
    // Trigger pulse for this agent on thinking event
    if (data.agent_id) {
      agentPulse.triggerPulse(data.agent_id)
      console.log(`✨ Pulsing agent ${data.agent_id} for thinking block`)
    }

    const lineNumber = eventStreamEntries.value.length + 1

    const entry: EventStreamEntry = {
      id: data.id || crypto.randomUUID(),
      lineNumber,
      sourceType: 'thinking_block',
      level: 'INFO',
      content: `Thinking: ${data.thinking.slice(0, 100)}${data.thinking.length > 100 ? '...' : ''}`,
      timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
      metadata: {
        data: data
      }
    }

    // Force Vue reactivity by replacing the array instead of mutating
    eventStreamEntries.value = [...eventStreamEntries.value, entry]
    console.log(`Added thinking block event`)
  }

  /**
   * Add tool use block event from WebSocket
   */
  function addToolUseBlockEvent(data: any) {
    // Trigger pulse for this agent on tool use event
    if (data.agent_id) {
      agentPulse.triggerPulse(data.agent_id)
      console.log(`✨ Pulsing agent ${data.agent_id} for tool use: ${data.tool_name}`)
    }

    const lineNumber = eventStreamEntries.value.length + 1

    const entry: EventStreamEntry = {
      id: data.id || crypto.randomUUID(),
      lineNumber,
      sourceType: 'tool_use_block',
      level: 'INFO',
      content: `Tool: ${data.tool_name}`,
      timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
      metadata: {
        data: data
      }
    }

    // Force Vue reactivity by replacing the array instead of mutating
    eventStreamEntries.value = [...eventStreamEntries.value, entry]
    console.log(`Added tool use block event: ${data.tool_name}`)
  }

  /**
   * Add thinking block to chat messages
   */
  function addThinkingToChatMessage(data: any) {
    console.log('[addThinkingToChatMessage] Creating thinking message:', data)

    const thinkingMessage: ChatMessage = {
      id: data.id || crypto.randomUUID(),
      sender: 'orchestrator',
      type: 'thinking',
      thinking: data.thinking,
      timestamp: data.timestamp || new Date().toISOString()
    }

    // Force Vue reactivity by replacing the array instead of mutating
    chatMessages.value = [...chatMessages.value, thinkingMessage]
    console.log(`[addThinkingToChatMessage] ✅ ADDED thinking to chat UI (${chatMessages.value.length} total)`)
  }

  /**
   * Add tool use block to chat messages
   */
  function addToolUseToChatMessage(data: any) {
    console.log('[addToolUseToChatMessage] Creating tool use message:', data)

    const toolUseMessage: ChatMessage = {
      id: data.id || crypto.randomUUID(),
      sender: 'orchestrator',
      type: 'tool_use',
      toolName: data.tool_name,
      toolInput: data.tool_input,
      timestamp: data.timestamp || new Date().toISOString()
    }

    console.log('[addToolUseToChatMessage] Tool use message created:', toolUseMessage)
    // Force Vue reactivity by replacing the array instead of mutating
    chatMessages.value = [...chatMessages.value, toolUseMessage]
    console.log(`[addToolUseToChatMessage] ✅ ADDED tool use to chat UI (${chatMessages.value.length} total): ${data.tool_name}`)
  }

  // Helper functions
  function mapEventCategoryToLevel(category: EventCategory, eventType: string): LogLevel | 'SUCCESS' {
    // Hook events are typically INFO unless they indicate errors
    if (category === 'hook') {
      if (eventType.toLowerCase().includes('error')) return 'ERROR'
      return 'INFO'
    }

    // Response events map based on event type
    if (eventType.toLowerCase().includes('error')) return 'ERROR'
    if (eventType.toLowerCase().includes('warn')) return 'WARNING'
    if (eventType.toLowerCase().includes('success')) return 'SUCCESS'
    if (eventType.toLowerCase().includes('debug')) return 'DEBUG'

    return 'INFO'
  }

  function extractTokensFromPayload(payload: Record<string, any>): number | undefined {
    // Extract token counts from payload if available
    const tokens = payload?.tokens || payload?.input_tokens || payload?.output_tokens
    return tokens ? Number(tokens) : undefined
  }

  // ═══════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════

  async function initialize() {
    console.log('Initializing orchestrator store...')

    // Initialize chat width from localStorage
    initializeChatWidth()

    // Fetch orchestrator info first to get real UUID
    try {
      const response = await chatService.getOrchestratorInfo()
      orchestratorAgentId.value = response.orchestrator.id
      orchestratorAgent.value = response.orchestrator
      console.log('Orchestrator info loaded:', orchestratorAgentId.value, 'Cost:', response.orchestrator.total_cost)
    } catch (error) {
      console.error('Failed to load orchestrator info:', error)
      // Fall back to a safe default behavior
      return
    }

    // Connect WebSocket
    connectWebSocket()

    // Load agents from API
    try {
      await loadAgents()
    } catch (error) {
      console.error('Failed to load agents:', error)
    }

    // Load chat history with real orchestrator ID
    try {
      await loadChatHistory()
    } catch (error) {
      console.error('Failed to load initial chat history:', error)
    }

    // Load event stream history
    try {
      await fetchEventHistory({ limit: DEFAULT_EVENT_HISTORY_LIMIT })
      console.log('Event stream history loaded')
    } catch (error) {
      console.error('Failed to load event stream history:', error)
    }

    console.log('Orchestrator store initialized')
  }

  // ═══════════════════════════════════════════════════════════
  // RETURN PUBLIC API
  // ═══════════════════════════════════════════════════════════

  return {
    // State
    agents,
    selectedAgentId,
    orchestratorAgentId,
    orchestratorAgent,
    eventStreamEntries,
    eventStreamFilter,
    autoScroll,
    fileTrackingEvents,
    chatMessages,
    chatWidth,
    isTyping,
    isConnected,
    commandInputVisible,
    autocompleteItems,
    autocompleteLoading,
    autocompleteError,
    websocketEventCount,
    // ADW State
    viewMode,
    adws,
    selectedAdwId,
    adwEvents,
    adwEventsByStep,
    allAdwEvents,
    allAdwEventsByStep,
    adwsLoading,
    adwEventsLoading,

    // Getters
    activeAgents,
    runningAgents,
    idleAgents,
    selectedAgent,
    filteredEventStream,
    stats,
    chatWidthPixels,
    hasAutocompleteItems,
    // ADW Getters
    selectedAdw,
    runningAdws,
    completedAdws,
    failedAdws,
    adwSteps,

    // Actions
    selectAgent,
    clearAgentSelection,
    loadAgents,
    addAgent,
    updateAgent,
    removeAgent,
    addEventStreamEntry,
    clearEventStream,
    setEventStreamFilter,
    toggleAutoScroll,
    toggleCommandInput,
    showCommandInput,
    hideCommandInput,
    exportEventStream,
    addChatMessage,
    sendUserMessage,
    clearChat,
    toggleChatWidth,
    initializeChatWidth,
    loadChatHistory,
    generateAutocomplete,
    updateAutocompleteHistory,
    clearAutocomplete,
    connectWebSocket,
    disconnectWebSocket,
    handleWebSocketMessage,
    initialize,

    // Event stream actions
    fetchEventHistory,
    addAgentLogEvent,
    addOrchestratorChatEvent,

    // Agent pulse actions (optimized for production)
    triggerAgentPulse: agentPulse.triggerPulse,
    isAgentPulsing: agentPulse.isAgentPulsing,
    getAgentPulseClass: agentPulse.getAgentPulseClass,
    getPulsingAgents: agentPulse.getPulsingAgents,
    isPulsing: agentPulse.isPulsing,  // Reactive Set for template bindings

    // ADW Actions
    setViewMode,
    toggleViewMode,
    fetchAdws,
    selectAdw,
    fetchAdwEvents
  }
})
